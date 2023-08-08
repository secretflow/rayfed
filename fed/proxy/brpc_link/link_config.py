import logging
from dataclasses import dataclass

from spu.libspu import link

from fed.config import CrossSiloMessageConfig


@dataclass
class BrpcLinkCrossSiloMessageConfig(CrossSiloMessageConfig):
    connect_retry_times: int = None
    connect_retry_interval_ms: int = None
    recv_timeout_ms: int = None
    http_timeout_ms: int = None
    http_max_payload_size: int = None
    throttle_window_size: int = None
    brpc_channel_protocol: str = None
    brpc_channel_connection_type: str = None

    def dump_to_link_desc(self, link_desc: link.Desc):
        if self.timeout_in_ms is not None:
            link_desc.http_timeout_ms = self.timeout_in_ms

        if self.connect_retry_times is not None:
            link_desc.connect_retry_times = self.connect_retry_times
        if self.connect_retry_interval_ms is not None:
            link_desc.connect_retry_interval_ms = self.connect_retry_interval_ms
        if self.recv_timeout_ms is not None:
            link_desc.recv_timeout_ms = self.recv_timeout_ms
        if self.http_timeout_ms is not None:
            logging.warning('http_timeout_ms and timeout_ms are set at the same time, '
                           f'http_timeout_ms {self.http_timeout_ms} will be used.')
            link_desc.http_timeout_ms = self.http_timeout_ms
        if self.http_max_payload_size is not None:
            link_desc.http_max_payload_size = self.http_max_payload_size
        if self.throttle_window_size is not None:
            link_desc.throttle_window_size = self.throttle_window_size
        if self.brpc_channel_protocol is not None:
            link_desc.brpc_channel_protocol = self.brpc_channel_protocol
        if self.brpc_channel_connection_type is not None:
            link_desc.brpc_channel_connection_type = self.brpc_channel_connection_type
        
        if not hasattr(link_desc, 'recv_timeout_ms'):
            # set default timeout 3600s
            link_desc.recv_timeout_ms = 3600 * 1000
        if not hasattr(link_desc, 'http_timeout_ms'):
            # set default timeout 120s
            link_desc.http_timeout_ms = 120 * 1000
    