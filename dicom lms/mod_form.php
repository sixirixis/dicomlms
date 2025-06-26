<?php
// This file is part of Moodle - http://moodle.org/

defined('MOODLE_INTERNAL') || die();

require_once($CFG->dirroot.'/course/moodleform_mod.php');

/**
 * Medical Imaging activity settings form
 */
class mod_medical_imaging_mod_form extends moodleform_mod {

    function definition() {
        global $CFG;

        $mform = $this->_form;

        // General section
        $mform->addElement('header', 'general', get_string('general', 'form'));

        $mform->addElement('text', 'name', get_string('name'), array('size' => '64'));
        if (!empty($CFG->formatstringstriptags)) {
            $mform->setType('name', PARAM_TEXT);
        } else {
            $mform->setType('name', PARAM_CLEANHTML);
        }
        $mform->addRule('name', null, 'required', null, 'client');
        $mform->addRule('name', get_string('maximumchars', '', 255), 'maxlength', 255, 'client');

        $this->standard_intro_elements();

        // Medical Imaging specific settings
        $mform->addElement('header', 'medical_imaging_settings', get_string('settings', 'mod_medical_imaging'));

        // Study type selection
        $types = medical_imaging_get_types();
        $mform->addElement('select', 'imaging_type', get_string('imaging_type', 'mod_medical_imaging'), $types);
        $mform->setDefault('imaging_type', 'dicom');
        $mform->addHelpButton('imaging_type', 'imaging_type', 'mod_medical_imaging');

        // Study UID input
        $mform->addElement('text', 'study_uid', get_string('study_uid', 'mod_medical_imaging'), array('size' => '80'));
        $mform->setType('study_uid', PARAM_TEXT);
        $mform->addRule('study_uid', null, 'required', null, 'client');
        $mform->addHelpButton('study_uid', 'study_uid', 'mod_medical_imaging');

        // Or select from available studies
        $studies = medical_imaging_get_orthanc_studies();
        if (!empty($studies)) {
            $study_options = array('' => get_string('choose...'));
            foreach ($studies as $uid => $study) {
                $study_options[$uid] = $study['description'] . ' (' . $study['patient'] . ')';
            }
            $mform->addElement('select', 'study_selector', get_string('select_study', 'mod_medical_imaging'), $study_options);
            $mform->addHelpButton('study_selector', 'select_study', 'mod_medical_imaging');
        }

        // Study description
        $mform->addElement('textarea', 'study_description', get_string('study_description', 'mod_medical_imaging'), 
                          array('rows' => 4, 'cols' => 80));
        $mform->setType('study_description', PARAM_TEXT);

        // Learning objectives
        $mform->addElement('textarea', 'learning_objectives', get_string('learning_objectives', 'mod_medical_imaging'), 
                          array('rows' => 4, 'cols' => 80));
        $mform->setType('learning_objectives', PARAM_TEXT);

        // Viewer settings
        $mform->addElement('header', 'viewer_settings', get_string('viewer_settings', 'mod_medical_imaging'));

        $mform->addElement('advcheckbox', 'enable_annotations', get_string('enable_annotations', 'mod_medical_imaging'));
        $mform->setDefault('enable_annotations', 1);

        $mform->addElement('advcheckbox', 'enable_measurements', get_string('enable_measurements', 'mod_medical_imaging'));
        $mform->setDefault('enable_measurements', 1);

        $mform->addElement('advcheckbox', 'enable_3d_rendering', get_string('enable_3d_rendering', 'mod_medical_imaging'));
        $mform->setDefault('enable_3d_rendering', 1);

        $mform->addElement('advcheckbox', 'track_viewing_time', get_string('track_viewing_time', 'mod_medical_imaging'));
        $mform->setDefault('track_viewing_time', 1);

        $mform->addElement('advcheckbox', 'require_annotation', get_string('require_annotation', 'mod_medical_imaging'));
        $mform->setDefault('require_annotation', 0);

        // Assessment settings
        $mform->addElement('header', 'assessment_settings', get_string('assessment_settings', 'mod_medical_imaging'));

        $mform->addElement('textarea', 'assessment_questions', get_string('assessment_questions', 'mod_medical_imaging'), 
                          array('rows' => 6, 'cols' => 80));
        $mform->setType('assessment_questions', PARAM_TEXT);
        $mform->addHelpButton('assessment_questions', 'assessment_questions', 'mod_medical_imaging');

        $mform->addElement('text', 'min_viewing_time', get_string('min_viewing_time', 'mod_medical_imaging'), 
                          array('size' => '10'));
        $mform->setType('min_viewing_time', PARAM_INT);
        $mform->setDefault('min_viewing_time', 300); // 5 minutes
        $mform->addHelpButton('min_viewing_time', 'min_viewing_time', 'mod_medical_imaging');

        // Standard coursemodule elements
        $this->standard_coursemodule_elements();

        // Standard buttons
        $this->add_action_buttons();
    }

    function data_preprocessing(&$default_values) {
        parent::data_preprocessing($default_values);
    }

    function validation($data, $files) {
        $errors = parent::validation($data, $files);

        // Validate study UID format
        if (!empty($data['study_uid'])) {
            if (!preg_match('/^[0-9.]+$/', $data['study_uid']) && !preg_match('/^WSI_/', $data['study_uid'])) {
                $errors['study_uid'] = get_string('invalid_study_uid', 'mod_medical_imaging');
            }
        }

        // Validate minimum viewing time
        if (isset($data['min_viewing_time']) && $data['min_viewing_time'] < 0) {
            $errors['min_viewing_time'] = get_string('invalid_min_viewing_time', 'mod_medical_imaging');
        }

        return $errors;
    }
}
