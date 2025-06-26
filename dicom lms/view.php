<?php
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
$event = \mod_medical_imaging\event\course_module_viewed::create(array(
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
