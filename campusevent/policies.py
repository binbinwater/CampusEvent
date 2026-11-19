from abc import ABC, abstractmethod


class RegistrationPolicy(ABC):
    """Stable abstraction for how a newly submitted registration starts."""

    policy_type: str
    display_name: str

    @abstractmethod
    def initial_status(self) -> str:
        """Return the registration status immediately after submission."""

    def __repr__(self):
        return f"<{type(self).__name__} policy_type={self.policy_type!r}>"


class DirectRegistrationPolicy(RegistrationPolicy):
    policy_type = "direct"
    display_name = "直接报名"

    def initial_status(self) -> str:
        return "approved"


class ReviewRegistrationPolicy(RegistrationPolicy):
    policy_type = "review"
    display_name = "管理员审核"

    def initial_status(self) -> str:
        return "pending"


POLICIES = {
    DirectRegistrationPolicy.policy_type: DirectRegistrationPolicy(),
    ReviewRegistrationPolicy.policy_type: ReviewRegistrationPolicy(),
}


def policy_for(policy_type: str) -> RegistrationPolicy:
    try:
        return POLICIES[policy_type]
    except KeyError as error:
        raise ValueError(f"未知报名方式：{policy_type}") from error