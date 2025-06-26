<?php
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
    $event = \mod_medical_imaging\event\course_module_instance_list_viewed::create(array(
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
