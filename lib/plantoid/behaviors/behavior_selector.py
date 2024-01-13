import lib.plantoid.behaviors.behavior_15 as behavior_15
import lib.plantoid.behaviors.behavior_14 as behavior_14

def get_plantoid_function(plantoid_number, fn_name):

    # TODO: add cases here

    print("PLANTOID NUMBER == ", plantoid_number)
    
    if plantoid_number == 15:

        fn_dict = {
            'create_seed_metadata': behavior_15.create_seed_metadata,
            'ingurgitate_crypto': behavior_15.ingurgitate_crypto
        }

    if plantoid_number == 14:
        fn_dict = {
            'create_seed_metadata': behavior_14.create_seed_metadata,
            'ingurgitate_crypto': behavior_14.ingurgitate_crypto
        }

    selected_function = fn_dict[fn_name]

    return selected_function