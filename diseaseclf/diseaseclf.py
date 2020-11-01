import os, joblib
PACKAGE_DIR = os.path.dirname(__file__)
import warnings
import numpy as np
warnings.filterwarnings('ignore')

class DiseaseClassifier(object):
    """ Disease classifier """
    def __init__(self, data_list ):
        super( DiseaseClassifier, self).__init__() 
        self.data_list = np.reshape(data_list, (-1,10) )



    def predict ( self, proba = False ):
        disease_model = open(os.path.join(PACKAGE_DIR,"models/model.pkl"),"rb")
        disease_clf = joblib.load(disease_model)
        if proba:
            diseases = ["Covid", "Fever", "Migrane", 'Cholera', 'No symptoms Found'  ]
            print( diseases )

            lst_dis = disease_clf.predict_proba( self.data_list ).tolist()[0]
            # print( lst_dis[ 0 ])

            comb = list(zip(lst_dis, diseases ))
            print([ 'you have ' + str(round(i[0], 3)*100) + '% chance of being infected with '+ i[1] for i in comb  ])
            
            return comb
    
        pred = disease_clf.predict( self.data_list )
        return list(pred)[0]
        

