from dataclasses import dataclass

from core.notifications.base import Notification, NotificationLevel


@dataclass(slots=True)
class RegistrationRequestAcceptedV1(Notification):
    type = "registration_request.accepted.v1"
    level = NotificationLevel.SUCCESS


@dataclass(slots=True)
class RegistrationRequestRejectedV1(Notification):
    type = "registration_request.rejected.v1"
    level = NotificationLevel.WARNING

    reject_reason: str


@dataclass(slots=True)
class ProductWarnedV1(Notification):
    type = "product.warned.v1"
    level = NotificationLevel.WARNING

    product_name: str
    article: str
    product_id: int
    reason: str
    complaint_id: int


@dataclass(slots=True)
class ProductBlockedV1(Notification):
    type = "product.blocked.v1"
    level = NotificationLevel.DANGER

    product_name: str
    article: str
    product_id: int
    reason: str
    complaint_id: int


@dataclass(slots=True)
class SellerWarnedV1(Notification):
    type = "seller.warned.v1"
    level = NotificationLevel.WARNING

    reason: str
    complaint_id: int


@dataclass(slots=True)
class SellerBlockedV1(Notification):
    type = "seller.blocked.v1"
    level = NotificationLevel.DANGER

    reason: str
    complaint_id: int


@dataclass(slots=True)
class SlotPurchaseSuccessV1(Notification):
    type = "slot_purchase.success.v1"
    level = NotificationLevel.SUCCESS

    index: int
    slot_id: int


@dataclass(slots=True)
class SlotPurchaseFailV1(Notification):
    type = "slot_purchase.fail.v1"
    level = NotificationLevel.DANGER

    index: int
    slot_id: int


@dataclass(slots=True)
class TopUpSuccessV1(Notification):
    type = "top_up.success.v1"
    level = NotificationLevel.SUCCESS

    amount: int
    currency: str
    balance: int


@dataclass(slots=True)
class ClientReturnRequestAcceptedV1(Notification):
    type = "client.return_request.accepted.v1"
    level = NotificationLevel.SUCCESS

    code: str
    order_id: int
    product_name: str
    product_id: int


@dataclass(slots=True)
class ClientReturnRequestRejectedV1(Notification):
    type = "client.return_request.rejected.v1"
    level = NotificationLevel.DANGER

    code: str
    order_id: int
    product_name: str
    product_id: int


@dataclass(slots=True)
class SellerReturnRequestAcceptedV1(Notification):
    type = "seller.return_request.accepted.v1"
    level = NotificationLevel.INFO

    code: str
    order_id: int
    product_name: str
    article: str
    product_id: int


@dataclass(slots=True)
class WithdrawalRequestPaidV1(Notification):
    type = "withdrawal_request.paid.v1"
    level = NotificationLevel.SUCCESS

    amount: int
    currency: str


@dataclass(slots=True)
class WithdrawalRequestRejectedV1(Notification):
    type = "withdrawal_request.rejected.v1"
    level = NotificationLevel.DANGER

    amount: int
    currency: str


@dataclass(slots=True)
class OrderItemDeliveredV1(Notification):
    type = "item.delivered.v1"
    level = NotificationLevel.SUCCESS
