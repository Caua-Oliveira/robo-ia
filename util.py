def transform_day_of_week(day_number):
    days_map = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado"
    }
    return days_map.get(day_number, "Dia inválido")


def transform_group(turma_number):
    turma_map = {
        0: "A",
        1: "B",
        2: "C"
    }
    return turma_map.get(turma_number, "Grupo inválido")