#!/usr/bin/env python3

import os.path
import os
import sys
import numpy as np
import neurom as nm
from neurom.core.types import NeuriteType
import json
from pprint import pprint

# Uses:
# https://github.com/BlueBrain/NeuroM
#
# some doc here:
# https://github.com/BlueBrain/NeuroM/blob/04f48747785265aa7a4f7b0750c1447cae408468/doc/source/definitions.rst#id1
# https://github.com/BlueBrain/NeuroM/blob/04f48747785265aa7a4f7b0750c1447cae408468/doc/source/definitions.rst


#print(sys.argv)
#exit()


def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)): #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def get_morph_data(file_name, recenter=True):
    ''' get the morphology data from neurom '''
    morph = nm.load_neuron(file_name)
    if recenter:
        transform = Translation(-morph.soma.center)
        morph = morph.transform(transform)

    data = morph._data.data_block  # pylint: disable=protected-access
    return morph, np.ascontiguousarray(data, dtype=np.float32)


def save_morph_as_json (input, output) :
    morph, data = get_morph_data(input, False)

    # these are just shorter names
    sections = []
    soma = {}

    morpho_to_export = {
        "sections": sections,
        "soma": soma
    }

    for section in morph.sections:
        # for types that have a polyline/polycylinder shape
        if section.type == NeuriteType.axon or section.type == NeuriteType.apical_dendrite or section.type == NeuriteType.basal_dendrite:
            points = []

            for point in section.points:
                current_point = {
                    "position": [point[0], point[1], point[2]],
                    "radius": point[3]
                }
                points.append(current_point)

            current_section = {
                "id": section.id,
                "parent": section.parent.id if section.parent else None,
                "children": list(map(lambda x: x.id, section.children)),
                "typename": section.type._name_,
                "typevalue": section.type._value_ - 1, # because enum are 1-indexed
                "points": points
            }

            sections.append( current_section )

        # for the some, the only section to have a polygonal shape
        elif section.type == NeuriteType.soma:
            soma["id"] = section.id
            soma["type"] = section.type._name_

            points = []
            for point in section.points[1:]:
                current_point = {
                    "position": [point[0], point[1], point[2]],
                }
                points.append(current_point)

            soma["points"] = points
            soma["radius"] = section.points[1,3]


            #print(np.shape( section.points )[0])

            #soma["center"] = [section.points[1:,0].mean(), section.points[1:,1].mean(), section.points[1:,2].mean() ]
            #soma["center"] = [section.points[0,0], section.points[0,1], section.points[0,2] ]
            #soma["center"] = [section.points[10][0], section.points[10][1], section.points[10][2]]
            #soma["radius"] = 5

            #soma["radius"] = ((section.points[1:,0].max() - section.points[1:,0].min() ) + (section.points[1:,1].max() - section.points[1:,1].min() ) + (section.points[1:,2].max() - section.points[1:,2].min() )) / 3


            # when single point. THE FIRST POINT IS FAKE!!
            #soma["center"] = [section.points[1,0], section.points[1,1], section.points[1,2] ]
            #soma["radius"] = section.points[1,3]
            #print(soma["radius"])
            #print([section.points[0][0], section.points[0][1], section.points[0][2]])

            #pprint(vars(section))



    json_data = json.dumps(morpho_to_export, ensure_ascii=True, indent=2)
    #json_data = json.dumps(morpho_to_export)
    f = open(output,'w')
    f.write(json_data)
    f.close()



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("At least one .asc file path is axpected as input")
        exit()

    for input_path in sys.argv[1:]:
        os.path.splitext(input_path)[0]+'.json'
        output_path = os.path.splitext(input_path)[0]+'.json'

        save_morph_as_json(input_path, output_path)
