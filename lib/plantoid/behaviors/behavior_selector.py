import lib.plantoid.behaviors.behavior_15 as behavior_15

def get_plantoid_function(plantoid_number, fn_name):

    # TODO: add cases here
    
    if plantoid_number == 15:

        fn_dict = {
            'create_seed_metadata': behavior_15.create_seed_metadata,
            'generate_oracle': behavior_15.generate_oracle
        }

    selected_function = fn_dict[fn_name]

    return selected_function