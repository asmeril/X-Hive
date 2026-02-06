import logging

from approval.approval_queue import approval_queue
from approval.telegram_notifier import TelegramApprovalNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main() -> None:
    notifier = TelegramApprovalNotifier(approval_queue)
    notifier.start_bot()


if __name__ == "__main__":
    main()
