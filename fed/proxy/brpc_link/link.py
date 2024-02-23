import logging
import threading
from typing import Dict

import cloudpickle
import spu.libspu.link as link

from fed.exceptions import FedRemoteError
from fed.proxy.barriers import (
    add_two_dim_dict,
    key_exists_in_two_dim_dict,
    pop_from_two_dim_dict,
)
from fed.proxy.base_proxy import SenderReceiverProxy
from fed.proxy.brpc_link.link_config import BrpcLinkCrossSiloMessageConfig

logger = logging.getLogger(__name__)


def _fill_link_ssl_opts(tls_config: Dict, link_ssl_opts: link.SSLOptions):
    ca_cert = tls_config['ca_cert']
    cert = tls_config['cert']
    key = tls_config['key']
    link_ssl_opts.cert.certificate_path = cert
    link_ssl_opts.cert.private_key_path = key
    link_ssl_opts.verify.ca_file_path = ca_cert
    link_ssl_opts.verify.verify_depth = 1


class BrpcLinkSenderReceiverProxy(SenderReceiverProxy):
    def __init__(
        self,
        addresses: Dict,
        self_party: str,
        tls_config: Dict = None,
        proxy_config: Dict = None,
    ) -> None:
        logging.info(f'brpc options: {proxy_config}')
        proxy_config = BrpcLinkCrossSiloMessageConfig.from_dict(proxy_config)
        super().__init__(addresses, self_party, tls_config, proxy_config)
        self._parties_rank = {
            party: i for i, party in enumerate(self._addresses.keys())
        }
        self._rank = list(self._addresses).index(self_party)

        desc = link.Desc()
        for party, addr in self._addresses.items():
            desc.add_party(party, addr)
        if tls_config:
            _fill_link_ssl_opts(tls_config, desc.server_ssl_opts)
            _fill_link_ssl_opts(tls_config, desc.client_ssl_opts)
        if isinstance(proxy_config, BrpcLinkCrossSiloMessageConfig):
            proxy_config.dump_to_link_desc(desc)
        self._desc = desc

        self._all_data = {}
        self._server_ready_with_msg = (False, '')
        self._server_ready_event = threading.Event()

    def start(self):
        try:
            self._linker = link.create_brpc(self._desc, self._rank)
            self._server_ready = (
                True,
                f'Succeeded to listen on {self._addresses[self._party]}.',
            )
            self._server_ready_event.set()

        except Exception as e:
            self._server_ready = (
                False,
                f'Failed to listen on {self._addresses[self._party]} as exception:\n{e}',
            )
            self._server_ready_event.set()

    def is_ready(self):
        self._server_ready_event.wait()
        return self._server_ready

    def send(self, dest_party, data, upstream_seq_id, downstream_seq_id):
        msg = {
            'upstream_seq_id': upstream_seq_id,
            'downstream_seq_id': downstream_seq_id,
            'payload': data,
        }
        msg_bytes = cloudpickle.dumps(msg)
        self._linker.send_async(self._parties_rank[dest_party], msg_bytes)

        return True

    def get_data(self, src_party, upstream_seq_id, curr_seq_id):
        data_log_msg = f"data for {curr_seq_id} from {upstream_seq_id} of {src_party}"
        logger.debug(f"Getting {data_log_msg}")
        all_data = self._all_data
        rank = self._parties_rank[src_party]
        if key_exists_in_two_dim_dict(all_data, upstream_seq_id, curr_seq_id):
            logger.debug(f"Getted {data_log_msg}.")
            data = pop_from_two_dim_dict(all_data, upstream_seq_id, curr_seq_id)
            if isinstance(data, FedRemoteError):
                logger.warn(
                    f"Receiving exception: {type(data)}, {data} from {src_party}, "
                    f"upstream_seq_id: {upstream_seq_id}, "
                    f"curr_seq_id: {curr_seq_id}. Re-raise it."
                )
                raise data
            return data

        while True:
            msg = self._linker.recv(rank)
            msg = cloudpickle.loads(msg)
            upstream_seq_id_in_msg = str(msg['upstream_seq_id'])
            downstream_seq_id_in_msg = str(msg['downstream_seq_id'])
            data = msg['payload']
            logger.debug(
                f"Received data for {downstream_seq_id_in_msg} from {upstream_seq_id_in_msg}."
            )
            if upstream_seq_id_in_msg == str(
                upstream_seq_id
            ) and downstream_seq_id_in_msg == str(curr_seq_id):
                logger.debug(f"Getted {data_log_msg}.")
                if isinstance(data, FedRemoteError):
                    logger.warn(
                        f"Receiving exception: {type(data)}, {data} from {src_party}, "
                        f"upstream_seq_id: {upstream_seq_id}, "
                        f"curr_seq_id: {curr_seq_id}. Re-raise it."
                    )
                    raise data
                return data
            else:
                add_two_dim_dict(
                    all_data, upstream_seq_id_in_msg, downstream_seq_id_in_msg, data
                )

    def stop(self):
        self._linker.stop_link()
