import signal

from fed._private import constants, global_context
from fed.config import get_cluster_config


def _signal_handler(signum, frame):
    global_context.clear_global_context()


class ActorWithComm:
    """For actor who wants to send message inside actor.
    
    Since global_context is initialized in main processor but actor in another
    processor has no the global context and can not do message sending.
    Every Actor should init its own global context and clean it during destroying
    (Ray will send SIGINT to actor before collecting it).
    """
    def __init__(self, job_name=constants.RAYFED_DEFAULT_JOB_NAME):
        signal.signal(signal.SIGINT, _signal_handler)
        current_party = get_cluster_config(job_name).current_party
        global_context.init_global_context(
            current_party=current_party, job_name=job_name
        )
