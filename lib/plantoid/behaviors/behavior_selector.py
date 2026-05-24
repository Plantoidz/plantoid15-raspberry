
import lib.plantoid.behaviors.behavior_21 as behavior_21
import lib.plantoid.behaviors.behavior_19 as behavior_19
import lib.plantoid.behaviors.behavior_17 as behavior_17
import lib.plantoid.behaviors.behavior_16 as behavior_16
import lib.plantoid.behaviors.behavior_15 as behavior_15
import lib.plantoid.behaviors.behavior_14 as behavior_14

def get_plantoid_function(plantoid_number, fn_name):

    # TODO: add cases here

    print("PLANTOID NUMBER == ", plantoid_number)

    if plantoid_number == 21:
        fn_dict = {
            'create_seed_metadata': behavior_21.create_seed_metadata,
            'ingurgitate_crypto': behavior_21.ingurgitate_crypto
    }

    elif plantoid_number == 19:
        fn_dict = {
            'create_seed_metadata': behavior_19.create_seed_metadata,
            'ingurgitate_crypto': behavior_19.ingurgitate_crypto
        }

    # elif plantoid_number == 18:
    #     fn_dict = {
    #         'create_seed_metadata': behavior_18.create_seed_metadata,
    #         'ingurgitate_crypto': behavior_18.ingurgitate_crypto
    #     }
    
    elif plantoid_number == 17:

        fn_dict = {
                'create_seed_metadata': behavior_17.create_seed_metadata,
                'ingurgitate_crypto': behavior_17.ingurgitate_crypto
        }

    elif plantoid_number == 16:

        fn_dict = {
            'create_seed_metadata': behavior_16.create_seed_metadata,
            'ingurgitate_crypto': behavior_16.ingurgitate_crypto
        }

    elif plantoid_number == 15:

        fn_dict = {
            'create_seed_metadata': behavior_15.create_seed_metadata,
            'ingurgitate_crypto': behavior_15.ingurgitate_crypto
        }

    elif plantoid_number == 14:
        fn_dict = {
            'create_seed_metadata': behavior_14.create_seed_metadata,
            'ingurgitate_crypto': behavior_14.ingurgitate_crypto
        }

    else:
        raise ValueError(f"No behavior dict defined for plantoid {plantoid_number}")

    
    return fn_dict[fn_name]

