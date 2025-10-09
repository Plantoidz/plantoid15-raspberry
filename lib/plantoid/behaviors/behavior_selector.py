import lib.plantoid.behaviors.behavior_16 as behavior_16
import lib.plantoid.behaviors.behavior_15 as behavior_15
import lib.plantoid.behaviors.behavior_14 as behavior_14
import lib.plantoid.behaviors.behavior_13 as behavior_13


def get_plantoid_function(plantoid_number, fn_name):

    # TODO: add cases here

    print("PLANTOID NUMBER == ", plantoid_number)
    
    if plantoid_number == 16:

        fn_dict = {
            'create_seed_metadata': behavior_16.create_seed_metadata,
            'ingurgitate_crypto': behavior_16.ingurgitate_crypto
        }

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
        
     if plantoid_number == 13:
        fn_dict = {
            'create_seed_metadata': behavior_13.create_seed_metadata,
            'ingurgitate_crypto': behavior_13.ingurgitate_crypto
        }

    selected_function = fn_dict[fn_name]

    return selected_function