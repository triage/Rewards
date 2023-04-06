
from redeem.transaction_approver import transaction_should_approve


class TestTransactionApprover:
    def test_should_approve_equal(self):
        assert transaction_should_approve(balance=100, transaction_amount=100)

    def test_should_approve(self):
        assert transaction_should_approve(balance=200, transaction_amount=100)

    def test_should_not_approve(self):
        assert not transaction_should_approve(balance=  50, transaction_amount=101)