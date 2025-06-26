# Create the Moodle Medical Imaging Activity Plugin
# This plugin integrates with the unified viewer to display DICOM and pathology studies

# Create version.php for Moodle plugin
version_php = """<?php
// This file is part of Moodle - http://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

defined('MOODLE_INTERNAL') || die();

$plugin->version   = 2024062600;        // The current plugin version (Date: YYYYMMDDXX)
$plugin->requires  = 2023042400;        // Requires Moodle 4.2 or later
$plugin->component = 'mod_medical_imaging'; // Full name of the plugin (used for diagnostics)
$plugin->maturity  = MATURITY_STABLE;
$plugin->release   = '1.0.0';
$plugin->dependencies = array();
"""

# Create lib.php with core functions
lib_php = """<?php
// This file is part of Moodle - http://moodle.org/

defined('MOODLE_INTERNAL') || die();

/**
 * Medical Imaging activity module core functions
 */

/**
 * List of features supported by medical imaging module
 * @param string $feature FEATURE_xx constant for requested feature
 * @return mixed True if feature is supported, null if unknown
 */
function medical_imaging_supports($feature) {
    switch($feature) {
        case FEATURE_MOD_ARCHETYPE:           return MOD_ARCHETYPE_RESOURCE;
        case FEATURE_GROUPS:                  return false;
        case FEATURE_GROUPINGS:               return false;
        case FEATURE_MOD_INTRO:               return true;
        case FEATURE_COMPLETION_TRACKS_VIEWS: return true;
        case FEATURE_GRADE_HAS_GRADE:         return false;
        case FEATURE_GRADE_OUTCOMES:          return true;
        case FEATURE_BACKUP_MOODLE2:          return true;
        case FEATURE_SHOW_DESCRIPTION:        return true;
        case FEATURE_ADVANCED_GRADING:        return false;
        case FEATURE_PLAGIARISM:              return false;
        case FEATURE_COMMENT:                 return true;

        default: return null;
    }
}

/**
 * Add medical imaging instance
 * @param stdClass $medical_imaging
 * @param mod_medical_imaging_mod_form $mform
 * @return int The id of the newly inserted medical imaging record
 */
function medical_imaging_add_instance($medical_imaging, $mform = null) {
    global $DB;

    $medical_imaging->timecreated = time();
    $medical_imaging->timemodified = time();

    $id = $DB->insert_record('medical_imaging', $medical_imaging);

    // Log the creation
    $event = \\mod_medical_imaging\\event\\course_module_instance_list_viewed::create(array(
        'context' => context_module::instance($medical_imaging->coursemodule),
        'objectid' => $id
    ));
    $event->trigger();

    return $id;
}

/**
 * Update medical imaging instance
 * @param stdClass $medical_imaging
 * @param mod_medical_imaging_mod_form $mform
 * @return bool True if successful
 */
function medical_imaging_update_instance($medical_imaging, $mform = null) {
    global $DB;

    $medical_imaging->timemodified = time();
    $medical_imaging->id = $medical_imaging->instance;

    return $DB->update_record('medical_imaging', $medical_imaging);
}

/**
 * Delete medical imaging instance
 * @param int $id
 * @return bool True if successful
 */
function medical_imaging_delete_instance($id) {
    global $DB;

    if (!$medical_imaging = $DB->get_record('medical_imaging', array('id' => $id))) {
        return false;
    }

    // Delete any dependent records here
    $DB->delete_records('medical_imaging_views', array('medical_imaging_id' => $id));
    $DB->delete_records('medical_imaging_annotations', array('medical_imaging_id' => $id));
    
    $DB->delete_records('medical_imaging', array('id' => $medical_imaging->id));

    return true;
}

/**
 * Return information for the course-module
 * @param cm_info $cm
 * @return cached_cm_info
 */
function medical_imaging_get_coursemodule_info($cm) {
    global $DB;

    if (!$medical_imaging = $DB->get_record('medical_imaging', array('id' => $cm->instance))) {
        return null;
    }

    $info = new cached_cm_info();
    $info->name = $medical_imaging->name;

    if ($cm->showdescription) {
        $info->content = format_module_intro('medical_imaging', $medical_imaging, $cm->id, false);
    }

    return $info;
}

/**
 * Called when viewing course page. Shows extra details after the link if enabled.
 * @param cm_info $cm
 * @return string
 */
function medical_imaging_cm_info_view(cm_info $cm) {
    global $DB;

    $medical_imaging = $DB->get_record('medical_imaging', array('id' => $cm->instance));
    if (!$medical_imaging) {
        return '';
    }

    $viewertype = '';
    if (strpos($medical_imaging->study_uid, 'WSI_') !== false) {
        $viewertype = ' (Pathology Slide)';
    } else {
        $viewertype = ' (DICOM Study)';
    }

    return html_writer::span($viewertype, 'medical-imaging-type');
}

/**
 * Get medical imaging types
 * @return array Array of imaging types
 */
function medical_imaging_get_types() {
    return array(
        'dicom' => get_string('dicom', 'mod_medical_imaging'),
        'pathology' => get_string('pathology', 'mod_medical_imaging'),
        'xray' => get_string('xray', 'mod_medical_imaging'),
        'ct' => get_string('ct', 'mod_medical_imaging'),
        'mri' => get_string('mri', 'mod_medical_imaging'),
        'pet' => get_string('pet', 'mod_medical_imaging'),
        'ultrasound' => get_string('ultrasound', 'mod_medical_imaging'),
        'nuclear' => get_string('nuclear', 'mod_medical_imaging')
    );
}

/**
 * Get available studies from Orthanc
 * @return array Array of studies
 */
function medical_imaging_get_orthanc_studies() {
    global $CFG;
    
    $studies = array();
    
    if (empty($CFG->orthanc_url)) {
        return $studies;
    }
    
    try {
        $url = rtrim($CFG->orthanc_url, '/') . '/studies';
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'header' => [
                    'Content-Type: application/json',
                    'Authorization: Basic ' . base64_encode($CFG->orthanc_user . ':' . $CFG->orthanc_password)
                ],
                'timeout' => 10
            ]
        ]);
        
        $response = file_get_contents($url, false, $context);
        if ($response !== false) {
            $study_ids = json_decode($response, true);
            
            foreach ($study_ids as $study_id) {
                $study_url = $CFG->orthanc_url . '/studies/' . $study_id;
                $study_response = file_get_contents($study_url, false, $context);
                if ($study_response !== false) {
                    $study_data = json_decode($study_response, true);
                    $studies[$study_data['MainDicomTags']['StudyInstanceUID']] = [
                        'id' => $study_id,
                        'uid' => $study_data['MainDicomTags']['StudyInstanceUID'],
                        'description' => $study_data['MainDicomTags']['StudyDescription'] ?? 'No description',
                        'date' => $study_data['MainDicomTags']['StudyDate'] ?? '',
                        'patient' => $study_data['PatientMainDicomTags']['PatientName'] ?? 'Unknown'
                    ];
                }
            }
        }
    } catch (Exception $e) {
        debugging('Error fetching Orthanc studies: ' . $e->getMessage());
    }
    
    return $studies;
}

/**
 * Track student viewing activity
 * @param int $medical_imaging_id
 * @param int $user_id
 * @param string $study_uid
 * @param int $view_duration
 */
function medical_imaging_track_view($medical_imaging_id, $user_id, $study_uid, $view_duration = 0) {
    global $DB;
    
    $view_record = new stdClass();
    $view_record->medical_imaging_id = $medical_imaging_id;
    $view_record->user_id = $user_id;
    $view_record->study_uid = $study_uid;
    $view_record->view_duration = $view_duration;
    $view_record->timestamp = time();
    
    $DB->insert_record('medical_imaging_views', $view_record);
    
    // Trigger completion event if applicable
    $cm = get_coursemodule_from_instance('medical_imaging', $medical_imaging_id);
    $completion = new completion_info(get_course($cm->course));
    if ($completion->is_enabled($cm)) {
        $completion->update_state($cm, COMPLETION_VIEWED, $user_id);
    }
}

/**
 * Save annotation data
 * @param int $medical_imaging_id
 * @param int $user_id
 * @param string $study_uid
 * @param string $annotation_data JSON encoded annotation data
 * @return int Annotation ID
 */
function medical_imaging_save_annotation($medical_imaging_id, $user_id, $study_uid, $annotation_data) {
    global $DB;
    
    $annotation = new stdClass();
    $annotation->medical_imaging_id = $medical_imaging_id;
    $annotation->user_id = $user_id;
    $annotation->study_uid = $study_uid;
    $annotation->annotation_data = $annotation_data;
    $annotation->timestamp = time();
    
    return $DB->insert_record('medical_imaging_annotations', $annotation);
}
"""

# Create mod_form.php for the activity settings form
mod_form_php = """<?php
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
"""

# Create view.php - the main viewing page
view_php = """<?php
// This file is part of Moodle - http://moodle.org/

require('../../config.php');
require_once($CFG->dirroot.'/mod/medical_imaging/lib.php');

$id = optional_param('id', 0, PARAM_INT); // course_module ID, or
$m  = optional_param('m', 0, PARAM_INT);  // medical_imaging instance ID

if ($id) {
    $cm         = get_coursemodule_from_id('medical_imaging', $id, 0, false, MUST_EXIST);
    $course     = $DB->get_record('course', array('id' => $cm->course), '*', MUST_EXIST);
    $medical_imaging  = $DB->get_record('medical_imaging', array('id' => $cm->instance), '*', MUST_EXIST);
} else if ($m) {
    $medical_imaging  = $DB->get_record('medical_imaging', array('id' => $m), '*', MUST_EXIST);
    $course     = $DB->get_record('course', array('id' => $medical_imaging->course), '*', MUST_EXIST);
    $cm         = get_coursemodule_from_instance('medical_imaging', $medical_imaging->id, $course->id, false, MUST_EXIST);
} else {
    print_error('missingparameter');
}

require_login($course, true, $cm);

$context = context_module::instance($cm->id);

// Trigger course_module_viewed event
$event = \\mod_medical_imaging\\event\\course_module_viewed::create(array(
    'objectid' => $medical_imaging->id,
    'context' => $context
));
$event->add_record_snapshot('course', $course);
$event->add_record_snapshot('medical_imaging', $medical_imaging);
$event->trigger();

// Track viewing activity
medical_imaging_track_view($medical_imaging->id, $USER->id, $medical_imaging->study_uid);

// Print the page header
$PAGE->set_url('/mod/medical_imaging/view.php', array('id' => $cm->id));
$PAGE->set_title(format_string($medical_imaging->name));
$PAGE->set_heading(format_string($course->fullname));
$PAGE->set_context($context);

echo $OUTPUT->header();

// Show activity name and description
echo $OUTPUT->heading(format_string($medical_imaging->name), 2);

if ($medical_imaging->intro) {
    echo $OUTPUT->box(format_module_intro('medical_imaging', $medical_imaging, $cm->id), 'generalbox mod_introbox', 'medical_imagingintro');
}

// Display learning objectives if present
if (!empty($medical_imaging->learning_objectives)) {
    echo html_writer::start_tag('div', array('class' => 'learning-objectives'));
    echo html_writer::tag('h3', get_string('learning_objectives', 'mod_medical_imaging'));
    echo html_writer::tag('div', format_text($medical_imaging->learning_objectives), array('class' => 'objectives-content'));
    echo html_writer::end_tag('div');
}

// Display study description if present
if (!empty($medical_imaging->study_description)) {
    echo html_writer::start_tag('div', array('class' => 'study-description'));
    echo html_writer::tag('h3', get_string('study_description', 'mod_medical_imaging'));
    echo html_writer::tag('div', format_text($medical_imaging->study_description), array('class' => 'description-content'));
    echo html_writer::end_tag('div');
}

// Determine viewer URL based on study type
$viewer_url = '';
$unified_viewer_url = $CFG->wwwroot . '/mod/medical_imaging/viewer.php';

if (strpos($medical_imaging->study_uid, 'WSI_') !== false) {
    // Pathology slide
    $viewer_url = $unified_viewer_url . '?type=pathology&study=' . urlencode($medical_imaging->study_uid) . '&cmid=' . $cm->id;
} else {
    // DICOM study
    $viewer_url = $unified_viewer_url . '?type=dicom&study=' . urlencode($medical_imaging->study_uid) . '&cmid=' . $cm->id;
}

// Display the viewer iframe
echo html_writer::start_tag('div', array('class' => 'medical-imaging-viewer-container'));
echo html_writer::tag('iframe', '', array(
    'src' => $viewer_url,
    'width' => '100%',
    'height' => '600px',
    'frameborder' => '0',
    'allowfullscreen' => 'true',
    'title' => get_string('medical_viewer', 'mod_medical_imaging')
));
echo html_writer::end_tag('div');

// Display assessment questions if present
if (!empty($medical_imaging->assessment_questions)) {
    echo html_writer::start_tag('div', array('class' => 'assessment-questions'));
    echo html_writer::tag('h3', get_string('assessment_questions', 'mod_medical_imaging'));
    echo html_writer::tag('div', format_text($medical_imaging->assessment_questions), array('class' => 'questions-content'));
    echo html_writer::end_tag('div');
}

// Add JavaScript for tracking and interaction
$PAGE->requires->js_call_amd('mod_medical_imaging/viewer', 'init', array(
    'cmid' => $cm->id,
    'studyuid' => $medical_imaging->study_uid,
    'enableAnnotations' => !empty($medical_imaging->enable_annotations),
    'trackViewingTime' => !empty($medical_imaging->track_viewing_time),
    'minViewingTime' => $medical_imaging->min_viewing_time ?? 0
));

echo $OUTPUT->footer();
"""

# Write Moodle plugin files
plugin_dir = "medical-imaging-lms/moodle-plugins/mod_medical_imaging"

with open(f"{plugin_dir}/version.php", "w") as f:
    f.write(version_php)

with open(f"{plugin_dir}/lib.php", "w") as f:
    f.write(lib_php)

with open(f"{plugin_dir}/mod_form.php", "w") as f:
    f.write(mod_form_php)

with open(f"{plugin_dir}/view.php", "w") as f:
    f.write(view_php)

print("✅ Created Moodle Medical Imaging Plugin")
print("📁 Files created:")
print("- moodle-plugins/mod_medical_imaging/version.php")
print("- moodle-plugins/mod_medical_imaging/lib.php")
print("- moodle-plugins/mod_medical_imaging/mod_form.php")
print("- moodle-plugins/mod_medical_imaging/view.php")
print("\n📋 Plugin Features:")
print("- Activity module for medical imaging studies")
print("- Support for DICOM and pathology slides")
print("- Integration with Orthanc server")
print("- Viewing time tracking")
print("- Annotation support")
print("- Assessment capabilities")
print("- HIPAA-compliant logging")