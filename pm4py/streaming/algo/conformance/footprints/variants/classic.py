from pm4py.util import constants, exec_utils, xes_constants
import logging
import pandas as pd


class Parameters:
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY


START_ACTIVITIES = "start_activities"
END_ACTIVITIES = "end_activities"
ACTIVITIES = "activities"
SEQUENCE = "sequence"
PARALLEL = "parallel"


class FootprintsStreamingConformance(object):
    def __init__(self, footprints, parameters=None):
        """
        Initialize the footprints streaming conformance object

        Parameters
        ---------------
        footprints
            Footprints
        parameters
            Parameters of the algorithm
        """
        self.footprints = footprints
        self.case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME)
        self.activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters,
                                                       xes_constants.DEFAULT_NAME_KEY)
        self.start_activities = footprints[START_ACTIVITIES]
        self.end_activities = footprints[END_ACTIVITIES]
        self.activities = footprints[ACTIVITIES]
        self.all_fps = set(footprints[SEQUENCE]).union(set(footprints[PARALLEL]))
        self.case_dict = {}
        self.dev_dict = {}

    def receive(self, event):
        """
        Receive an event from the live stream

        Parameters
        ---------------
        event
            Event (dictionary)
        """
        self.check(event)

    def check(self, event):
        """
        Check an event and updates the case dictionary

        Parameters
        ----------------
        event
            Event (dictionary)
        """
        case = event[self.case_id_key] if self.case_id_key in event else None
        activity = event[self.activity_key] if self.activity_key in event else None
        if case is not None and activity is not None:
            self.verify_footprints(case, activity)
        else:
            self.message_case_or_activity_not_in_event(event)

    def verify_footprints(self, case, activity):
        """
        Verify the event according to the footprints
        (assuming it has a case and an activity)

        Parameters
        ----------------
        case
            Case ID
        activity
            Activity
        """
        if case not in self.case_dict:
            self.dev_dict[case] = 0
        if activity in self.activities:
            if case not in self.case_dict:
                self.verify_start_case(case, activity)
            else:
                self.verify_intra_case(case, activity)
            self.case_dict[case] = activity
        else:
            self.dev_dict[case] += 1
            self.message_activity_not_possible(activity, case)

    def verify_intra_case(self, case, activity):
        """
        Verify the footprints of the current event

        Parameters
        ----------------
        case
            Case
        activity
            Activity
        """
        prev = self.case_dict[case]
        df = (prev, activity)
        if df not in self.all_fps:
            self.dev_dict[case] += 1
            self.message_footprints_not_possible(df, case)

    def verify_start_case(self, case, activity):
        """
        Verify the start activity of a case

        Parameters
        ---------------
        case
            Case
        activity
            Activity
        """
        if activity not in self.start_activities:
            self.dev_dict[case] += 1
            self.message_start_activity_not_possible(activity, case)

    def get_status(self, case):
        """
        Gets the current status of a case

        Parameters
        -----------------
        case
            Case

        Returns
        -----------------
        boolean
            Boolean value (True if there are no deviations)
        """
        if case in self.case_dict:
            num_dev = self.dev_dict[case]
            if num_dev == 0:
                return True
            else:
                return False
        else:
            self.message_case_not_in_dictionary(case)

    def terminate(self, case):
        """
        Terminate a case (checking its end activity)

        Parameters
        -----------------
        case
            Case

        Returns
        -----------------
        boolean
            Boolean value (True if there are no deviations)
        """
        if case in self.case_dict:
            curr = self.case_dict[case]
            if curr not in self.end_activities:
                self.message_end_activity_not_possible(curr, case)
                self.dev_dict[case] += 1
            num_dev = self.dev_dict[case]
            del self.case_dict[case]
            del self.dev_dict[case]
            if num_dev == 0:
                return True
            else:
                return False
        else:
            self.message_case_not_in_dictionary(case)

    def terminate_all(self):
        """
        Terminate all cases
        """
        cases = list(self.case_dict.keys())
        for case in cases:
            self.terminate(case)

    def message_case_or_activity_not_in_event(self, event):
        """
        Sends a message if the case or the activity are not
        there in the event
        """
        logging.error("case or activities are none! " + str(event))

    def message_activity_not_possible(self, activity, case):
        """
        Sends a message if the activity is not contained in the footprints

        Parameters
        --------------
        activity
            Activity
        case
            Case
        """
        logging.error(
            "the activity " + str(activity) + " is not possible according to the footprints! case: " + str(case))

    def message_footprints_not_possible(self, df, case):
        """
        Sends a message if the directly-follows between two activities is
        not possible

        Parameters
        ---------------
        df
            Directly-follows relations
        case
            Case
        """
        logging.error("the footprints " + str(df) + " are not possible! case: " + str(case))

    def message_start_activity_not_possible(self, activity, case):
        """
        Sends a message if the activity is not a possible start activity

        Parameters
        ---------------
        activity
            Activity
        case
            Case
        """
        logging.error("the activity " + str(activity) + " is not a possible start activity! case: " + str(case))

    def message_end_activity_not_possible(self, activity, case):
        """
        Sends a message if the activity is not a possible end activity

        Parameters
        ----------------
        activity
            Activity
        case
            Case
        """
        logging.error("the activity " + str(activity) + " is not a possible end activity! case: " + str(case))

    def message_case_not_in_dictionary(self, case):
        """
        Sends a message if the case is not in the current dictionary

        Parameters
        ----------------
        case
            Case
        """
        logging.error("the case " + str(case) + " is not in the dictionary! case: " + str(case))

    def get_diagnostics_dataframe(self):
        """
        Gets a diagnostics dataframe with the status of the cases

        Returns
        -------
        diagn_df
            Diagnostics dataframe
        """
        cases = list(self.case_dict.keys())

        diagn_stream = []

        for case in cases:
            status = self.get_status(case)
            diagn_stream.append({"case": case, "is_fit": status})

        return pd.DataFrame(diagn_stream)


def apply(footprints, parameters=None):
    """
    Gets a footprints conformance checking object

    Parameters
    --------------
    footprints
        Footprints object
    parameters
        Parameters of the algorithm

    Returns
    --------------
    fp_check_obj
        Footprints conformance checking object
    """
    if parameters is None:
        parameters = {}

    return FootprintsStreamingConformance(footprints, parameters=parameters)
