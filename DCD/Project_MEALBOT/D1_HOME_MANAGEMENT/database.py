
homes = []


def save(home):
    homes.append(home)


def list_homes():
    return homes


def find_resident_by_phone(phone):
    normalized_phone = phone.strip()

    for home in homes:
        for resident in home.residents:
            if resident.phone == normalized_phone:
                return resident

    return None
