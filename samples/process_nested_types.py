from sync_module.tools import process_nested_fields_df

if __name__ == "__main__":
    from sync_module.mi import get_remote_solution
    from sync_module.tools import collection_to_df

    # solution = get_remote_solution("ricoh_tyrens_sverige_250091618ed84de1957c2")
    solution = get_remote_solution("fjordhaven7")

    a = collection_to_df(solution.areas)

    b = process_nested_fields_df(a)

    b
