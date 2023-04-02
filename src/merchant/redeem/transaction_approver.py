def transaction_should_approve(balance: int, transaction_amount: int) -> bool:
    """
    Return if all the requirements are met which allow this transaction to proceed.
    For now, this just tracks if the user has sufficient balance.
    Ideally, this is split into its own module
    """
    return transaction_amount <= balance
