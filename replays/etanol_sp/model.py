"""Preço normal do etanol: sem o evento, o preço das próximas semanas seria o da última semana conhecida."""


def normal(history):
    return history[-1]
