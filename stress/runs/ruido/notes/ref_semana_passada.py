"""Ingênuo sazonal: vendas do mesmo dia da semana, 7 dias atrás."""


def predict(history, today):
    return history[-7]["vendas"]
