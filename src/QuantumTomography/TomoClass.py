from __future__ import print_function
from .TomoFunctions import *
from .TomoHelpers import *
import numpy as np
from scipy.optimize import leastsq

"""
Copyright 2020 University of Illinois Board of Trustees.
Licensed under the terms of an MIT license
"""

__author__ = 'Quoleon/Turro'
"""CHECK OUT THE REFERENCE PAGE ON OUR WEBSITE :
http://research.physics.illinois.edu/QI/Photonics/Quantum-Tomography_lib_Ref/"""


"""
    class Tomography()
    Desc: This is the main tomography object that the library is built around. The goal is to only have one tomography object and edit the
    configuration settings as you go.
    """
class Tomography():

    # # # # # # # # # # # #
    '''Public Variables'''
    # # # # # # # # # # # #

    # conf['NQubits']: >= 1, it will take a much longer time for more qubits.
    # conf['NDetectors']: 1 or 2
    # conf['Crosstalk']: [[C0->0, C0->1], [C1->0, C1->1]]
    # conf['Bellstate']: 'no' or 'yes'
    # conf['DoDriftCorrection'] = 'no' or 'yes'
    # conf['DoAccidentalCorrection'] = 'no' or 'yes'
    # conf['DoErrorEstimation']: >= 0
    # conf['Window']: 0 or array like, dimension = 1
    # conf['Efficiency']: 0 or array like, dimension = 1
    # conf['Beta']: 0 to 0.5, depending on purity of state and total number of measurements.

    # tomo_input: array like, dimension = 2.
    # input data of the last tomography run.

    # For n detectors:
    # tomo_input[:, 0]: times
    # tomo_input[:, np.arange(1, n_qubit+1)]: singles
    # tomo_input[:, n_qubit+1]: coincidences
    # tomo_input[:, np.arange(n_qubit+2, 3*n_qubit+2)]: measurements
    #
    # For 2n detectors:
    # tomo_input[:, 0]: times
    # tomo_input[:, np.arange(1, 2*n_qubit+1)]: singles
    # tomo_input[:, np.arange(2*n_qubit+1, 2**n_qubit+2*n_qubit+1)]: coincidences
    # tomo_input[:, np.arange(2**n_qubit+2*n_qubit+1, 2**n_qubit+4*n_qubit+1)]: measurements

    # last_rho: The predicted density matrix of the last tomography run.
    # last_intensity: The predicted intensity of the state for the last tomography run.
    # last_fval: The final value of the internal optimization function for the last tomography run.
    # mont_carl_states: The generated monte carlo states. 0 if no states have been generated yet.
    # intensity: Relative pump power (arb. units) during measurement for the last tomography run.
    # err_functions: These are the properties that you want to be calculated when getProperties is called.

    # # # # # # # # # #
    '''Constructors'''
    # # # # # # # # # #

    """
    Default Constructor
    Desc: This initializes a default tomography object
    """
    def __init__(self,nQ = 2):
        self.conf = {'NQubits': nQ,
            'NDetectors': 1,
            'Crosstalk': np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
            'Bellstate': 0,
            'DoDriftCorrection': 0,
            'DoAccidentalCorrection' : 0,
            'DoErrorEstimation': 0,
            'Window': 0,
            'Efficiency': 0,
            'RhoStart': [],
            'Beta': 0}
        self.err_functions = ['concurrence', 'tangle', 'entropy', 'linear_entropy', 'negativity', 'purity']

    """
    setConfSetting(setting, val)
    Desc: Sets a specific self.conf setting

    Parameters
    ----------
    setting : string
        The setting you want to update.
        Possible values are ['NQubits', 'NDetectors', 'Crosstalk', 'Bellstate', 'DoDriftCorrection', 'DoAccidentalCorrection', 'DoErrorEstimation', 'Window', 'Efficiency', 'RhoStart', 'Beta']
    val: ndarray, int, or string
            The new value you want to the setting to be.
    """
    def setConfSetting(self, setting, val):
        try:
            valC = val.copy()
        except:
            valC = val
        if (isinstance(val, str)):
            if (valC.lower() == "yes" or val.lower() == "true"):
                valC = 1
            elif (valC.lower() == "no" or val.lower() == "false"):
                valC = 0
        self.conf[setting] = valC

    """
    importConf(conftxt)
    Desc: Import a text file containing the configuration settings.

    Parameters
    ----------
    conftxt : string
        path to configuration file
    """
    def importConf(self, conftxt):
        conf = self.conf
        exec(compile(open(conftxt, "rb").read(), conftxt, 'exec'))
        self.standardizeConf()

    """
   importData(datatxt)
   Desc: Import a text file containing the tomography data and run tomography.

   Parameters
   ----------
   datatxt : string
       path to data file
   Returns
    -------
    rhog : ndarray with shape = (2^numQubits, 2^numQubits)
        The predicted density matrix.
    intensity : float
        The predicted overall intensity used to normalize the state.
    fvalp : float
        Final value of the internal optimization function. Values greater than the number
        of measurements indicate poor agreement with a quantum state.
   """
    def importData(self, datatxt):
        exec(compile(open(datatxt, "rb").read(), datatxt, 'exec'))
        return self.state_tomography(locals().get('tomo_input'), locals().get('intensity'))

    """
    importEval(evaltxt)
    Desc: Import a eval file containing the tomography data and the configuration setting, then run tomography.

    Parameters
    ----------
    evaltxt : string
        path to eval file
    Returns
    -------
    rhog : ndarray with shape = (2^numQubits, 2^numQubits)
        The predicted density matrix.
    intensity : float
        The predicted overall intensity used to normalize the state.
    fvalp : float
        Final value of the internal optimization function. Values greater than the number
        of measurements indicate poor agreement with a quantum state.
    """
    def importEval(self, evaltxt):
        conf = self.conf
        exec(compile(open(evaltxt, "rb").read(), evaltxt, 'exec'))
        self.standardizeConf()
        return self.state_tomography(locals().get('tomo_input'), locals().get('intensity'))
    """
    standardizeConf()
    Desc: Helper function to handle different cases of conf inputs
    """
    def standardizeConf(self):
        for k in self.conf.keys():
            if (isinstance(self.conf[k], str)):
                if (self.conf[k].lower() == "yes" or self.conf[k].lower() == "true"):
                    self.conf[k] = 1
                elif (self.conf[k].lower() == "no" or self.conf[k].lower() == "false"):
                    self.conf[k] = 0

    # # # # # # # # # # # # # #
    '''Tomography Functions'''
    # # # # # # # # # # # # # #

    """
    state_tomography(tomo_input, intensities)
    Desc: Main function that runs tomography.
    TODO: add method to comment
    Parameters
    ----------
    tomo_input : ndarray
        The input data for the current tomography. This is what tomo_input will be set to. Example can be seen at top of page. 
        See getTomoInputTemplate() to get a template for this input.
    intensities : 1darray with length = number of measurements
        Relative pump power (arb. units) during measurement; used for drift correction. Default will be an array of ones
    Returns
    -------
    rhog : ndarray with shape = (2^numQubits, 2^numQubits)
        The predicted density matrix.
    intensity : The predicted overall intensity used to normalize the state.
        The predicted overall intensity used to normalize the state. 
    fvalp : float
        Final value of the internal optimization function. Values greater than the number
        of measurements indicate poor agreement with a quantum state.
    """
    def state_tomography(self, tomo_input, intensities = -1,method="MLE"):

        # define a uniform intenstiy if not stated
        if (isinstance(intensities, int)):
            self.intensities = np.ones(tomo_input.shape[0])
        elif(len(intensities.shape) == 1 and intensities.shape[0] == tomo_input.shape[0]):
            self.intensities = intensities
        else:
            raise ValueError("Invalid intensities array")

        # filter the data
        [coincidences, measurements_densities, measurements_pures, accidentals] = self.filter_data(tomo_input)

        # get the starting state from linear_tomography if not defined
        starting_matrix = self.conf['RhoStart']
        if not starting_matrix:
            starting_matrix = self.linear_tomography(coincidences, measurements_pures)[0]

        # Currently linear tomography gets the phase wrong. So a temporary fix is to just transpose it.
        starting_matrix = starting_matrix.transpose()

        if(method == "MLE"):
            # perform MLE tomography
            [rhog, intensity, fvalp] = self.maximum_likelihood_tomography(starting_matrix, coincidences, measurements_densities, accidentals)
        else:
            # perform Bayesian tomography
            [rhog, intensity, fvalp] = self.bayesian_tomography(starting_matrix, coincidences, measurements_densities,accidentals)
        # save the results
        self.last_rho = rhog.copy()
        self.last_intensity = intensity
        self.last_fval = fvalp

        # TODO: Figure out why this is here.
        self.mont_carl_states = 0

        return [rhog, intensity, fvalp]

    """
        state_tomo(measurements, counts)
        todo:comment
        """
    def state_tomo(self,measurements,counts,crosstalk=-1,efficiency=0,time=-1,singles=-1,window=0,error=0, intensities=-1):
        tomo_input = self.buildTomoInput(measurements, counts, crosstalk, efficiency, time, singles,window,error)
        return self.state_tomography(tomo_input, intensities)




    """
    maximum_likelihood_tomography(starting_matrix, coincidences, m, acc)
    Desc: Calculates the most likely state given the data.

    Parameters
    ----------
    starting_matrix : ndarray with shape = (2^numQubits, 2^numQubits)
        The starting predicted state found with linear tomography.
    coincidences : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The counts of the tomography.
    m : ndarray with shape = (2^numQubits, 2^numQubits, number of measurements)
        The measurements of the tomography in density matrix form.
    acc : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The singles values of the tomography. Used for accidental correction.
    Returns
    -------
    rhog : ndarray with shape = (2^numQubits, 2^numQubits)
        The predicted density matrix.
    intensity : float
        The predicted overall intensity used to normalize the state.
    fvalp : float
        Final value of the internal optimization function. Values greater than the number
        of measurements indicate poor agreement with a quantum state.
    """
    def maximum_likelihood_tomography(self, starting_matrix, coincidences, m, accidentals):
        starting_matrix = make_positive(starting_matrix)
        starting_matrix = starting_matrix /np.trace(starting_matrix)
        init_intensity = np.mean(np.multiply(coincidences, 1/self.intensities)) * (starting_matrix.shape[0])
        starting_tvals = density2t(starting_matrix)
        n_t = len(starting_tvals)
        # np.multiply(coincidences, self.intensities)
        # t_to_density(starting_tvals)
        starting_tvals = starting_tvals + 0.0001
        starting_tvals = starting_tvals * np.sqrt(init_intensity)

        coincidences = np.real(coincidences)
        coincidences = coincidences.flatten()

        bet = self.conf['Beta']
        # n_data = np.shape(coincidences)[0]


        prediction = np.zeros(m.shape[2]) + 0j

        if bet == 0:
            final_tvals = leastsq(self.maxlike_fitness, np.real(starting_tvals), args = (coincidences, accidentals, m, prediction))[0]
            fvalp = np.sum(self.maxlike_fitness(final_tvals, coincidences, accidentals, m, prediction) ** 2)
        else:
            final_tvals = \
            leastsq(self.maxlike_fitness_hedged, np.real(starting_tvals), args = (coincidences, accidentals, m, prediction, bet))[0]
            fvalp = np.sum(self.maxlike_fitness_hedged(final_tvals, coincidences, accidentals, m, prediction, bet) ** 2)

        final_matrix = t_to_density(final_tvals)
        intensity = np.trace(final_matrix)
        final_matrix = final_matrix / np.trace(final_matrix)

        intensity = np.float64(np.real(intensity))

        return [final_matrix, intensity, fvalp]

    """
    maxlike_fitness(t, coincidences, accidentals, m, prediction)
    Desc: Calculates the diffrence between the current predicted state data and the actual data.

    Parameters
    ----------
    t : ndarray
        T values of the current predicted state.
    coincidences : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The counts of the tomography.
    accidentals : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The singles values of the tomography. Used for accidental correction.
    m : ndarray with shape = (2^numQubits, 2^numQubits, number of measurements)
        The measurements of the tomography in density matrix form.
    prediction : ndarray
        Predicted counts from the predicted state.

    Returns
    -------
    val : float
        value of the optimization function.
    """
    def maxlike_fitness(self, t, coincidences, accidentals, m, prediction):

        rhog = t_to_density(t)

        for j in range(len(prediction)):
            prediction[j] = np.float64(np.real(self.intensities[j] * np.real(np.trace(np.dot(m[:, :, j], rhog))) + accidentals[j]))
            prediction[j] = np.max([prediction[j], 0.01])
        val = (prediction - coincidences) / np.sqrt(prediction)

        val = np.float64(np.real(val))

        return val


    """
    maxlike_fitness_hedged(t, coincidences, accidentals, m, prediction, bet)
    Desc: Calculates the diffrence between the current predicted state data and the actual data using hedged maximum likelihood.

    Parameters
    ----------
    t : ndarray
        T values of the current predicted state.
    coincidences : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The counts of the tomography.
    accidentals : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The singles values of the tomography. Used for accidental correction.
    m : ndarray with shape = (2^numQubits, 2^numQubits, number of measurements)
        The measurements of the tomography in density matrix form .
    prediction : ndarray
        Predicted counts from the predicted state.
    bet : float 0 to .5
        The beta value used.

    Returns
    -------
    val : float
        value of the optimization function.
    """
    def maxlike_fitness_hedged(self, t, coincidences, accidentals, m, prediction, bet):

        rhog = t_to_density(t)

        for j in range(len(prediction)):
            prediction[j] = self.intensities[j] * np.real(np.trace(np.dot(m[:, :, j], rhog))) + accidentals[j]
            prediction[j] = np.max([prediction[j], 0.01])

        hedge = np.repeat(np.real((bet * np.log(np.linalg.det(np.mat(rhog)))) / len(prediction)), len(prediction))
        val = np.sqrt(np.real((((prediction - coincidences) ** 2) / (2 * prediction)) - hedge) + 1000)

        val = np.float64(np.real(val))

        return val


    # TODO add comments for bayesian tomography
    def bayesian_tomography(self, starting_matrix, coincidences, m, accidentals):
        starting_matrix = make_positive(starting_matrix)
        starting_matrix = starting_matrix / np.trace(starting_matrix)
        init_intensity = np.mean(np.multiply(coincidences, 1 / self.intensities)) * (starting_matrix.shape[0])
        starting_tvals = density2t(starting_matrix)
        n_t = len(starting_tvals)
        # np.multiply(coincidences, self.intensities)
        # t_to_density(starting_tvals)
        starting_tvals = starting_tvals + 0.0001
        starting_tvals = starting_tvals * np.sqrt(init_intensity)

        coincidences = np.real(coincidences)
        coincidences = coincidences.flatten()

        bet = self.conf['Beta']
        # n_data = np.shape(coincidences)[0]

        # redefine m
        # measurement_basis =

        # Outputs needed
        # final_tvals, fvalp
        # final_tvals = leastsq(self.maxlike_fitness, np.real(starting_tvals), args=(coincidences, accidentals, m, prediction))[0]
        # fvalp = np.sum(self.maxlike_fitness(final_tvals, coincidences, accidentals, m, prediction) ** 2)


        # Uniform Samples
        #------------------
        numMonteCarloSamples = 1000

        # Need to sample mixed states too. Currently only pure states are sampled for uniform
        monteCarloStates = np.array([toDensity(random_pure_state(self.conf["NQubits"])) for x in range(0,numMonteCarloSamples)])

        mean_density = np.zeros_like(starting_matrix)
        for state in monteCarloStates:
            mean_density += state * self.prob_D_given_P_gaussian(state, coincidences,m,accidentals,self.intensities)

        normalizationConstant = np.trace(mean_density)
        mean_density = mean_density / normalizationConstant
        mean_tvals = density2t(mean_density)
        var_tvals = np.zeros((len(mean_tvals),len(mean_tvals)))
        for state in monteCarloStates:
            var_tvals += np.outer(density2t(state)-mean_tvals,density2t(state)-mean_tvals) * self.prob_D_given_P_gaussian(state, coincidences,m,accidentals,init_intensity)

        var_tvals = var_tvals / normalizationConstant


        mean_density_normal = mean_density.copy()

        # Updated prior Samples
        # ------------------
        monteCarloTvals = np.random.multivariate_normal(mean_tvals, var_tvals, numMonteCarloSamples)

        mean_density = np.zeros_like(starting_matrix)
        for tvals in monteCarloTvals:
            state = t_to_density(tvals)
            mean_density += state * self.prob_D_given_P_gaussian(state, coincidences,m,accidentals,init_intensity)

        normalizationConstant = np.trace(mean_density)
        mean_density = mean_density / normalizationConstant
        mean_tvals = density2t(mean_density)
        var_tvals = np.zeros((len(mean_tvals), len(mean_tvals)))
        for tvals in monteCarloTvals:
            var_tvals += np.outer(tvals - mean_tvals,tvals - mean_tvals) * self.prob_D_given_P_gaussian(t_to_density(tvals), coincidences, m,accidentals,init_intensity)

        var_tvals = var_tvals / normalizationConstant



        intensity = init_intensity
        intensity = np.float64(np.real(intensity))
        fvalp = self.prob_D_given_P_gaussian(mean_density, coincidences,m,accidentals,init_intensity)
        return [mean_density, intensity, fvalp]

    # todo: comment
    def prob_D_given_P_binomial(self,givenState,coincidences,measurments,accidentals):
        total_prob = 1
        for j in range(coincidences.shape[0]):
            probMeas = np.real(np.trace(np.dot(measurments[:, :, j], givenState)))
            nSamples = np.float64(np.real(self.intensities[j] * np.real(np.trace(np.dot(measurments[:, :, j], givenState))) + accidentals[j]))

            total_prob *= probMeas ** Counts[x] * (1 - probMeas) ** (nSamples - Counts[x])
        return 0

    # todo: comment
    def prob_D_given_P_gaussian(self,givenState,coincidences,measurments,accidentals,intensities):

        Averages = np.zeros(measurments.shape[2]) + 0j

        for j in range(coincidences.shape[0]):
            # Averages[j] = inten0*np.float64(np.real(self.intensities[j] * np.real(np.trace(np.dot(measurments[:, :, j], givenState))) + accidentals[j]))
            Averages[j] =  intensities[j]*np.trace(measurments[:, :, j] @ givenState)
            if(Averages[j]==0):
                Averages[j] = np.max([Averages[j], 0.0000001])

        val = (Averages - coincidences)**2 / (2*Averages)
        val = np.float64(np.real(val))
        prob = np.exp(-1*np.sum(val),dtype=np.longdouble)
        return prob


    """
    linear_tomography(coincidences, measurements)
    Desc: Uses linear techniques to find a starting state for maximum likelihood estimation.
    TODO: idk what this is based off of. Does it even do the correct thing?
    Parameters
    ----------
    coincidences : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The counts of the tomography.
    measurements : ndarray with shape = (number of measurements, 2*numQubits)
        The measurements of the tomography in pure state form .

    Returns
    -------
    rhog : ndarray with shape = (2^numQubits, 2^numQubits)
        The starting predicted state.
    intensity : float
        The predicted overall intensity used to normalize the state.
    """
    def linear_tomography(self, coincidences, measurements, m_set = ()):
        if m_set == ():
            m_set = independent_set(measurements)
        if np.isscalar(m_set):
            n = len(coincidences)
            linear_measurements = measurements
            linear_data = coincidences

        else:
            n = np.int(np.sum(m_set))
            linear_measurements = measurements[(np.rot90(m_set == 1.0)[0])]
            linear_data = coincidences[(np.rot90(m_set == 1.0)[0])]

        linear_rhog = np.zeros([measurements.shape[1], measurements.shape[1]])

        b = b_matrix(linear_measurements)
        b_inv = np.linalg.inv(b)

        m = np.zeros([measurements.shape[1], measurements.shape[1], n]) + 0j
        for j in range(n):
            m[:, :, j] = m_matrix(j, linear_measurements, b_inv)
            linear_rhog = linear_rhog + linear_data[j] * m[:, :, j]

        intensity = np.trace(linear_rhog)
        rhog = linear_rhog / intensity

        return [rhog, intensity]

    """
    filter_data(tomo_input, intensities)
    Desc: Filters the data into separate arrays.
    TODO: edit intensities out of comment
    
    Parameters
    ----------
    tomo_input : ndarray
        The input data for the current tomography. This is what self.tomo_input will be set to. Example can be seen at top of page. 
        See getTomoInputTemplate() to get a template for this input.
    intensities : 1darray with length = number of measurements
        Relative pump power (arb. units) during measurement; used for drift correction.

    Returns
    -------
    data : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The counts/coincidences of the tomography.
    measurements_densities : ndarray with shape = (2^numQubits, 2^numQubits, number of measurements)
        The measurements of the tomography in density matrix form.
    measurements_pures : ndarray with shape = (number of measurements, 2*numQubits)
        The measurements of the tomography in pure state form.
    acc : ndarray with length = number of measurements or shape = (number of measurements, 2^numQubits) for 2 det/qubit
        The singles values of the tomography. Used for accidental correction.
    """
    def filter_data(self, tomo_input):
        # getting variables
        self.input = tomo_input

        nbits = self.conf['NQubits']
        ndet = self.conf['NDetectors']

        # time values
        t = tomo_input[:, 0]

        # singles values
        n_singles = self.getNumSingles()
        # sings = tomo_input[:, np.arange(n_singles) + 1]
        sings = self.getSingles()

        # coincidences
        n_coinc = self.getNumCoinc()
        coinc = self.getCoincidences()

        # settings
        settings = tomo_input[:, np.arange(n_singles + n_coinc + 1, len(tomo_input[0]))]

        # Set Efficiency is not already defined
        if (isinstance(self.conf['Efficiency'], int)):
            self.conf['Efficiency'] = np.ones(2 ** nbits)
        eff = self.conf['Efficiency'][0:2 ** nbits]

        # Set window is not already defined
        if (isinstance(self.conf['Window'], int)):
            self.conf['Window'] = np.ones(n_coinc)
        eff = self.conf['Window'][0:n_coinc]

        # Accidental Correction
        acc = np.zeros_like(coinc)
        if(self.conf['DoAccidentalCorrection'] == 1):
            window = self.conf['Window']
            if np.isscalar(window):
                window = window*np.ones(n_coinc)
            scalerIndex = np.concatenate((np.ones(nbits - 2), [2, 2]))
            additiveIndex = np.array([0, 1])
            for j in range(2, nbits):
                additiveIndex = np.concatenate(([2*j], additiveIndex))
            if (len(coinc.shape) == 1):
                acc = acc[:, np.newaxis]
            for j in range(n_coinc):
                index = bin(j).split("b")[1]
                index = "0" * (nbits - len(index)) + index
                index = [int(char) for char in index]
                index = index*scalerIndex + additiveIndex
                index = np.array(index, dtype = int)
                acc[:, j] = np.prod(np.real(sings[:, tuple(index)]), axis = 1) * (window[j] * 1e-9 / np.real(t)) ** (nbits - 1)
            if (acc.shape != coinc.shape):
                acc = acc[:, 0]

        # crosstalk
        ctalk = np.array(self.conf['Crosstalk'])[0:2 ** nbits, 0:2 ** nbits]

        # This chunk of code handles edge cases of the input of the crosstalk matrix.
        # The important crosstalk matrix is the big_crosstalk
        crosstalk = ctalk
        if np.ndim(ctalk) >= 3:
            for j in range(ctalk.shape[2]):
                crosstalk[j] = ctalk[:, :, j]
        if (ctalk == []):
            big_crosstalk = np.eye(2 ** nbits)
        else:
            big_crosstalk = crosstalk[:]
        big_crosstalk = big_crosstalk * np.outer(eff, np.ones(n_coinc))

        # Get measurements
        # Todo: this is very messy but works...? At some point it can be cleaned up, so that toDensity is used 
        # and the shapes are similar. The axis of the measuremennts_densities is kinda wonky. Not similar to measurements_pures
        measurements_densities = np.zeros([2 ** nbits, 2 ** nbits, np.prod(coinc.shape)],dtype=complex)
        measurements_pures = np.zeros([np.prod(coinc.shape), 2 ** nbits],dtype=complex)
        for j in range(coinc.shape[0]):
            m_twiddle = np.zeros([2 ** nbits, 2 ** nbits, 2 ** nbits]) + 0j
            u = 1
            for k in range(nbits):
                alpha = settings[j][2 * k]
                beta = settings[j][2 * k + 1]
                psi_k = np.array([alpha, beta])
                psip_k = np.array([np.conj(beta), np.conj(-alpha)])
                u_k = np.outer((np.array([1, 0])), psi_k) + np.outer((np.array([0, 1])), psip_k)
                # Changed from tensor_product to np.kron
                u = np.kron(u, u_k)
            if (ndet == 1):
                for k in range(0, 2 ** nbits):
                    m_twiddle[k, :, :] = np.outer(u[:, k].conj().transpose(), u[:, k])

                measurements_pures[j * n_coinc, :] = u[:, 0].conj().transpose()
                for k in range(1):
                    for l in range(2 ** nbits):
                        measurements_densities[:, :, j + k] = measurements_densities[:, :, j + k] + m_twiddle[l, :, :] * big_crosstalk[k, l]
                coincidences = coinc

            else:
                for k in range(2 ** nbits):
                    m_twiddle[k, :, :] = np.outer(u[:, k].conj().transpose(), u[:, k])
                    measurements_pures[j * n_coinc + k, :] = u[:, k].conj().transpose()
                for k in range(2 ** nbits):
                    for l in range(2 ** nbits):
                        measurements_densities[:, :, j * (2 ** nbits) + k] = measurements_densities[:, :, j * (2 ** nbits) + k] + m_twiddle[l, :, :] * \
                                                        big_crosstalk[k, l]

                coincidences = coinc.reshape((np.prod(coinc.shape), 1))
                acc = acc.reshape((np.prod(acc.shape), 1))


        return [coincidences, measurements_densities, measurements_pures, acc]

    """
        buildTomoInput(tomo_input, intensities)
        TODO: Test and write comment for this"""
    def buildTomoInput(self, measurements, counts, crosstalk, efficiency,time,singles,window, error):
        ################
        # measurements #
        ################
        # Get the number of qubits based on the measurement matrix
        if (len(measurements.shape)!=2 or measurements.shape[1]%2 != 0):
            raise ValueError("Invalid measurements matrix")
        else:
            self.conf['NQubits'] = int(measurements.shape[1]/2)
        # TODO: make sure measurements span the entire space

        ##########
        # counts #
        ##########
        # Check if counts has right dimensions
        if (counts.shape[0] != measurements.shape[0]):
            raise ValueError("Number of Counts does not match the number of measurements")
        # Determine if 2det/qubit from counts matrix
        try:
            if(counts.shape[1] == 1):
                self.conf['NDetectors'] = 1
            elif(counts.shape[1] == self.conf['NQubits']*2):
                self.conf['NDetectors'] = 2
            else:
                raise ValueError("The second axis of counts does not have the right dimension. Should be 1 or 2*NQubits for 2det")
        except:
            self.conf['NDetectors'] = 1

        ##############
        # efficiency #
        ##############
        if((not isinstance(efficiency, int)) and (len(efficiency.shape) !=1 or efficiency.shape[0] != self.conf['NQubits']*2)):
            raise ValueError("Invalid efficiency array. Length should be NQubits*2")
        else:
            self.conf['Efficiency'] = efficiency

        ##########
        # window #
        ##########
        if ((not isinstance(window, int)) and (len(window.shape) != 1 or window.shape[0] != self.getNumCoinc())):
            raise ValueError("Invalid window array. Length should be NQubits*NDetectors")
        else:
            self.conf['Window'] = window

        ################
        # time/singles #
        ################
        if ((not isinstance(time, int)) or (not isinstance(singles, int)) or (not isinstance(window, int))):
            self.conf['DoAccidentalCorrection'] = 1
            # Check if time has right length
            if (isinstance(time, int)):
                time = np.ones(measurements.shape[0])
            elif not (len(time.shape) == 1 and time.shape[0] == measurements.shape[0]):
                ValueError("Invalid time array")
            # Check if singles has right dimensions
            if (isinstance(singles, int)):
                singles = np.zeros((measurements.shape[0],2*self.conf["NQubits"]))
            elif not (len(singles.shape) == 2 and singles.shape[0] == measurements.shape[0] and singles.shape[1] == 2*self.conf["NQubits"]):
                raise ValueError("Invalid singles matrix")
            # Check if window has right length
            if (isinstance(window, int)):
                self.conf['Window'] = window
            elif (len(window.shape) == 1 and window.shape[0] == self.getNumCoinc()):
                self.conf['Window'] = window
            else:
                raise ValueError("Invalid window array")
        else:
            time = np.ones(measurements.shape[0])
            singles = np.zeros((measurements.shape[0],self.conf["NQubits"]))
            self.conf['Window'] = window


        #############
        # crosstalk #
        #############
        if (isinstance(crosstalk, int)):
            self.conf['Crosstalk'] = np.identity(2 ** self.conf["NQubits"])
        elif (len(crosstalk.shape) == 2 and crosstalk.shape[0] == crosstalk.shape[1] and crosstalk.shape[0] == 2 ** self.conf["NQubits"] ):
            self.conf['Crosstalk'] =  crosstalk
        else:
            raise ValueError("Invalid crosstalk matrix")

        #########
        # error #
        #########
        self.conf['DoErrorEstimation'] = error

        ##############
        # tomo_input #
        ##############
        # Here we build the tomo_input matrix and then return this to be fed to state_tomography
        tomo_input = 0
        n_qubit = self.conf['NQubits']
        if (self.conf['NDetectors'] == 1):
            tomo_input = np.zeros((measurements.shape[0], 3 * n_qubit + 2), dtype=complex)
            # times
            tomo_input[:, 0] = time
            # singles
            tomo_input[:, 1: n_qubit + 1] = singles
            # counts
            tomo_input[:, n_qubit + 1] = counts
            # measurements
            tomo_input[:, n_qubit + 2: 3 * n_qubit + 2] = measurements
        else:
            tomo_input = np.zeros((measurements.shape[0], 2 ** n_qubit + 4 * n_qubit + 1), dtype=complex)
            # times
            tomo_input[:, 0] = times
            # singles
            tomo_input[:, 1: 2 * n_qubit + 1] = singles
            # counts
            tomo_input[:, 2 * n_qubit + 1: 2 ** n_qubit + 2 * n_qubit + 1] = counts
            # measurements
            tomo_input[:, 2 ** n_qubit + 2 * n_qubit + 1: 2 ** n_qubit + 4 * n_qubit + 1] = measurements


        return tomo_input

    # # # # # # # # # #
    '''Get Functions'''
    # # # # # # # # # #


    """
    getNumCoinc()
    Desc: Returns the number of coincidences per measurement for the current configurations.
    """
    def getNumCoinc(self):
        if (self.conf['NDetectors'] == 2):
            return 2 ** self.conf['NQubits']
        else:
            return 1

    """
    getNumSingles()
    Desc: Returns the number of singles per measurement for the current configurations.
    """
    def getNumSingles(self):
        if (self.conf['NDetectors'] == 2):
            return 2 * self.conf['NQubits']
        else:
           return self.conf['NQubits']

    """
    getCoincidences()
    Desc: Returns an array of counts for all the measurments.
    """
    def getCoincidences(self):
        if (self.conf['NDetectors'] == 2):
            return self.input[:, np.arange(2*self.conf['NQubits']+1, 2**self.conf['NQubits']+2*self.conf['NQubits']+1)]
        else:
            return self.input[:, self.conf['NQubits']+1]

    """
    getSingles()
    Desc: Returns an array of singles for all the measurments.
    """
    def getSingles(self):
        if (self.conf['NDetectors'] == 2):
            return self.input[:, np.arange(1, 2*self.conf['NQubits']+1)]
        else:
            return self.input[:, np.arange(1, self.conf['NQubits']+1)]

    """
    getTimes()
    Desc: Returns an array of times for all the measurments.
    """
    def getTimes(self):
        return self.tomo_input[:, 0]

    """
        getMeasurements()
        Desc: Returns an array of measurements in pure state form for all the measurments.
        """
    def getMeasurements(self):
        if (self.conf['NDetectors'] == 2):
            return self.input[:, np.arange(2**self.conf['NQubits']+2*self.conf['NQubits']+1, 2**self.conf['NQubits']+4*self.conf['NQubits']+1)]
        else:
            return self.input[:, np.arange(self.conf['NQubits']+2, 3*self.conf['NQubits']+2)]

    """
    getNumBits()
    Desc: returns the number of qubits for the current configurations.
    """
    def getNumBits(self):
        return self.conf['NQubits']

    """
    getNumDetPerQubit()
    Desc: returns the number of detectors per qubit for the current configurations.
    """
    def getNumDetPerQubit(self):
        return self.conf['NDetectors']

    """
    getNumOfDetectorsTotal()
    Desc: Returns the total number of detectors for the current configurations.
    """
    def getNumOfDetectorsTotal(self):
        return self.getNumDetPerQubit()*self.getNumBits()

    """
    numBits(numBits)
    Desc: Returns an array of standard measurments in pure state form for the given number of qubits.
    TODO: edit comment to add numDet
    Parameters
    ----------
    numBits : int
        number of qubits you want for each measurement. Default will use the number of qubits in the current configurations.
    """
    def getBasisMeas(self, numBits = -1,numDet = -1):
        # check if numBits is an int
        if not (isinstance(numBits, int)):
            raise ValueError("numBits must be an integer")
        if(numBits < 1):
            numBits = self.getNumBits()

        # check if numDet is not 1 or 2
        if not (numDet in [-1, 1, 2]):
            raise ValueError("numDet must be an 1 or 2")
        if (numDet < 1):
            numDet = self.getNumDetPerQubit()

        # Define start meas basis
        if(numDet == 1):
            basis = np.array([[1, 0],
                              [0, 1],
                              [(2 ** (-1 / 2)), (2 ** (-1 / 2))],
                              [(2 ** (-1 / 2)), -(2 ** (-1 / 2))],
                              [(2 ** (-1 / 2)), (2 ** (-1 / 2)) * 1j],
                              [(2 ** (-1 / 2)), -(2 ** (-1 / 2)) * 1j]],dtype=complex)
        else:
            basis = np.array([[1, 0],
                              [(2 ** (-1 / 2)), (2 ** (-1 / 2))],
                              [(2 ** (-1 / 2)), (2 ** (-1 / 2)) * 1j]], dtype=complex)
        numBasis = basis.shape[0]
        m = np.zeros((numBasis ** numBits, 2 * numBits), dtype = complex)
        for i in range(m.shape[0]):
            for j in range(0, m.shape[1], 2):
                bitNumber = np.floor((m.shape[1] - j - 1) / 2)
                index = int(((i) / numBasis ** (bitNumber)) % numBasis)

                m[i, j] = basis[index][0]
                m[i, j + 1] = basis[index][1]
        return m

    """
    getTomoInputTemplate()
    Desc: returns a standard template for tomo_input for the given number of qubits.
    TODO: edit this comment for numDet
    Parameters
    ----------
    numBits : int
        number of qubits you want for each measurement. Default will use the number of qubits in the current configurations.

    Returns
    ----------
    Tomoinput : ndarray
        The input data for the current tomography. This is what tomo_input will be set to. Example can be seen at top of page. 
        See getTomoInputTemplate() to get a template for this input.
    """
    def getTomoInputTemplate(self, numBits = -1,numDet = -1):
        # check if numBits is an int
        if not (isinstance(numBits, int)):
            raise ValueError("numBits must be an integer")
        if (numBits < 1):
            numBits = self.getNumBits()

        # check if numDet is not 1 or 2
        if not(numDet in [-1,1,2]):
            raise ValueError("numDet must be an 1 or 2")
        if (numDet < 1):
            numDet = self.getNumDetPerQubit()

        measurements = self.getBasisMeas(numBits,numDet)

        if(numDet == 1):
            # For n detectors:
            Tomoinput = np.zeros((6**numBits, 3*numBits+2), dtype = complex)

            # input[:, n_qubit+1]: coincidences
            # coincidences left zeros

            # input[:, np.arange(n_qubit+2, 3*n_qubit+2)]: measurements
            Tomoinput[:, np.arange(numBits + 2, 3 * numBits + 2)] = measurements

        else:
            # For 2n detectors:
            Tomoinput = np.zeros((3**numBits, 2**numBits+4*numBits+1), dtype = complex)

            # input[:, np.arange(2*n_qubit+1, 2**n_qubit+2*n_qubit+1)]: coincidences
            # coincidences left zeros

            # input[:, np.arange(2**n_qubit+2*n_qubit+1, 2**n_qubit+4*n_qubit+1)]: measurements
            Tomoinput[:, np.arange(2**numBits+2*numBits+1, 2**numBits+4*numBits+1)] = measurements

        # tomo_input[:, 0]: times
        Tomoinput[:, 0] = np.ones_like(Tomoinput[:, 0])

        # tomo_input[:, np.arange(1, 2 * n_qubit + 1)]: singles
        # singles left zero
        return Tomoinput

    # # # # # # # # # # #
    '''ERROR FUNCTIONS'''
    # # # # # # # # # # #

    """
    getProperties(rho, bounds)
    Desc: Returns all the properties of the given density matrix.
          Using bounds will not change the conf settings. The calculated properties are determined by self.err_functions.

    Parameters
    ----------
    rho : ndarray with shape = (2^numQubits, 2^numQubits)
        The density matrix you would like to know the properties of.
    bounds : boolean
        Set this to true if you want error bounds on your estimated property values. Default is False.
        These are determined with monte carlo simulation and the states are saved under self.mont_carl_states

    Returns
    -------
    vals : ndarray with shape = (length of self.err_functions, 2)
        The first col is the name of the property.
        The second col is the value of the property.
        The third col is the error bound on the property.
    """
    def getProperties(self, rho, bounds = -1):
        # if bounds not set use the conf settings
        if(type(bounds) == int):
            bounds = (self.conf['DoErrorEstimation'] > 1) or self.mont_carl_states != 0
        if (bounds):
            # check if given state is of the current data
            if(fidelity(self.last_rho, rho) < .95):
                raise ValueError("Input data needed. You can only calculate bounds on the state used in the tomography.")
            err_n = self.conf['DoErrorEstimation']
            # increase err_n if needed
            if(err_n<= 1):
                err_n = 2
            # generate states if needed
            if(self.mont_carl_states == 0):
                states = self.tomography_states_generator(err_n)
            else:
                states = self.mont_carl_states
                err_n = len(states[1])
            vals1 = np.array([["intensity", np.mean(np.hstack((states[1], self.last_intensity))),
                               np.std(np.hstack((states[1], self.last_intensity)), ddof = err_n-1)],
                              ["fval", np.mean(np.hstack((states[2], self.last_fval))),
                               np.std(np.hstack((states[2], self.last_fval)), ddof = err_n-1)]], dtype = "O")
            vals2 = getProperties_helper_bounds(self.err_functions, states[0], rho)
        else:
            vals1 = np.array([["intensity", self.last_intensity], ["fval", self.last_fval]], dtype = "O")
            vals2 = getProperties_helper(self.err_functions, rho)



        vals = np.concatenate((vals1, vals2))
        return vals



    """
    tomography_states_generator(n)
    Desc: Uses monte carlo simulation to create random states similar to the estimated state.
          The states are also saved under self.mont_carl_states

    Parameters
    ----------
    n : int
        Number of approximate states you want to create.
        If no value is given it will use the conf settings.
    Returns
    -------
    rhop : ndarray with shape = (n, 2^numQubits, 2^numQubits)
        The approximate density matrices.
    intenp : ndarray with length = n
        The intensity of each approximate density matrices.
    fvalp : ndarray with length = n
        The fval of the regression associated with each approximate density matrices.
    """
    def tomography_states_generator(self, n = -1):
        if(n <= 1):
            n = max(self.conf['DoErrorEstimation'], 2)
        last_outPut = [self.last_rho, self.last_intensity, self.last_fval]

        ndet = self.conf['NDetectors']
        nbits = self.conf['NQubits']
        acc = self.conf['DoAccidentalCorrection']
        rhop = np.zeros([n, 2 ** nbits, 2 ** nbits]) + 0j
        intenp = np.zeros(n)
        fvalp = np.zeros(n)
        length = len(self.tomo_input[:, 0])
        if ndet == 1:
            time = np.reshape(self.tomo_input[:, 0], (length, 1))
            meas = self.tomo_input[:, np.arange(nbits + 2, len(self.tomo_input[0, :]))]
            for j in range(n):
                test_data = np.zeros([length, nbits + 1])
                if acc:
                    kk = range(nbits + 1)
                else:
                    kk = np.array([nbits])
                for k in kk:
                    for l in range(length):
                        test_data[l, k] = np.random.poisson(np.real(self.tomo_input[l, k + 1]))

                test_data = np.concatenate((time, test_data, meas), axis = 1)

                [rhop[j, :, :], intenp[j], fvalp[j]] = self.state_tomography(test_data, self.intensities)

        elif ndet == 2:
            time = np.reshape(self.tomo_input[:, 0], (length, 1))
            meas = self.tomo_input[:, np.arange(nbits + 2 ** nbits + 1, len(self.tomo_input[0, :]))]
            for j in range(n):
                test_data = np.zeros([length, nbits + 2 ** nbits])
                if acc:
                    kk = range(nbits + 2 ** nbits)
                else:
                    kk = np.arange(nbits, nbits + 2 ** nbits)
                for k in kk:
                    for l in range(length):
                        test_data[l, k] = np.random.poisson(np.real(self.tomo_input[l, k + 1]))

                test_data = np.concatenate((time, test_data, meas), axis = 1)

                [rhop[j, :, :], intenp[j], fvalp[j]] = self.state_tomography(test_data, intensities)[0]

        [self.last_rho, self.last_intensity, self.last_fval] = last_outPut
        self.mont_carl_states = [rhop, intenp, fvalp]
        return [rhop, intenp, fvalp]

    """
        getBellSettings(rho, bounds = -1)
        Desc: Returns the optimal measurment settings for the CHSH bell inequality.
              Using bounds will not change the conf settings.

        DISCLAIMER : In Progress, have not checked.

        Parameters
        ----------
        rho : ndarray with shape = (2^numQubits, 2^numQubits)
            The density matrix you would like to know the optimal bell measurment settings of.
        bounds : boolean
            Set this to true if you want error bounds on your estimated measurment settings. Default will use the conf settings.
            These are determined with monte carlo simulation and the states are saved under self.mont_carl_states

        Returns
        -------
        vals : ndarray with shape = (length of self.err_functions, 2 or 3)
            The first col is the associated side
            The second col is the detector settings on the associated side.
            The third col is the error bound on the detector settings.
        """
    def getBellSettings(self, rho, partsize_init = 9, partsize = 5, t = 3, bounds = -1):
        # if bounds not set use the conf settings
        if (type(bounds) == int):
            bounds = (self.conf['DoErrorEstimation'] > 1) or self.mont_carl_states != 0
        if (bounds):
            # check if given state is of the current data
            if (fidelity(self.last_rho, rho) < .95):
                raise ValueError("Input data needed. You can only calculate bounds on the state used in the tomography.")
            err_n = self.conf['DoErrorEstimation']
            # increase err_n if needed
            if (err_n <= 1):
                err_n = 2
            # generate states if needed
            if (self.mont_carl_states == 0):
                states = self.tomography_states_generator(err_n)
            else:
                states = self.mont_carl_states
                err_n = len(states[1])
            vals = getBellSettings_helper_bounds(states[0], rho, partsize_init, partsize, t, err_n)
        else:
            vals = getBellSettings_helper(rho, partsize_init, partsize, t)
        return vals
