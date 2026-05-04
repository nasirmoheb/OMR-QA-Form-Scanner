# Requirements Document

## Introduction

This document specifies the requirements for the OMR QA Form Scanner desktop application. The application performs batch Optical Mark Recognition on scanned Quality Assurance forms using pure computer vision techniques (no OCR). It processes a folder of scanned form images, extracts checkbox selections using pixel density analysis, stores aggregated results in memory, and generates interactive Plotly HTML analytics reports.

## Glossary

- **OMR**: Optical Mark Recognition - technology to detect presence of marks on paper
- **Fiducial_Marker**: One of four thick black squares located at the corners of the form, used for image alignment
- **Perspective_Transform**: Matrix transformation to flatten a skewed/form-scanned image to a standardized size
- **Checkbox_Region**: A rectangular area containing a single checkbox that may contain a mark
- **Pixel_Density**: The ratio of dark pixels to total pixels in a checkbox region, used to determine if the checkbox is marked
- **QA_Form**: Quality Assurance form with 14 questions and 3 answer columns (Yes/Somewhat/No)
- **Input_Folder**: Directory containing scanned form images (.jpg or .png)
- **Satisfaction_Score**: Weighted average score calculated as (Yes × 100 + Somewhat × 50 + No × 0) / Total Responses
- **Invalid_Form**: A scanned form where 0 or >1 checkboxes are marked for any question row

## Requirements

### Requirement 1: Image Input Selection

**User Story:** As a QA administrator, I want to select a folder containing scanned form images, so that the application can process multiple forms in batch.

#### Acceptance Criteria

1. THE Application SHALL provide a folder selection mechanism allowing the user to browse and select an Input_Folder
2. THE Application SHALL validate that the selected folder exists and is accessible
3. THE Application SHALL scan the selected folder and identify all files with .jpg or .png extensions
4. THE Application SHALL display the count of identified form images to the user before processing begins

### Requirement 2: Form Image Alignment Using Fiducial Markers

**User Story:** As a QA administrator, I want the application to automatically align scanned forms, so that checkbox positions are accurate regardless of how the form was scanned.

#### Acceptance Criteria

1. THE Vision_Processor SHALL detect exactly 4 fiducial markers in each form image
2. WHEN 4 fiducial markers are detected, THE Vision_Processor SHALL calculate a perspective transform matrix from the marker positions to a standardized 800x1000 pixel output
3. WHEN fewer than 4 fiducial markers are detected, THE Vision_Processor SHALL flag the form as Invalid_Form
4. WHEN more than 4 fiducial markers are detected, THE Vision_Processor SHALL select the 4 markers that form the largest rectangular area and use them for alignment

### Requirement 3: Checkbox Grid Detection and Reading

**User Story:** As a QA administrator, I want the application to read checkbox selections from aligned forms, so that I can analyze QA responses without manual data entry.

#### Acceptance Criteria

1. THE Vision_Processor SHALL divide the aligned image into a grid of 14 rows and 3 columns corresponding to the question checkboxes
2. FOR each checkbox region, THE Vision_Processor SHALL calculate the pixel density of dark pixels
3. THE Vision_Processor SHALL use a threshold of 0.15 (15% dark pixels) to determine if a checkbox is marked
4. FOR each question row (1-14), THE Application SHALL determine which column (Yes, Somewhat, No) contains a mark based on the highest pixel density above the threshold
5. WHEN 0 checkboxes are above the threshold for a question row, THE Application SHALL mark that question as "Invalid"
6. WHEN more than 1 checkbox is above the threshold for a question row, THE Application SHALL mark that question as "Invalid"

### Requirement 4: Batch Processing

**User Story:** As a QA administrator, I want the application to process multiple forms automatically, so that I can analyze large batches of QA forms efficiently.

#### Acceptance Criteria

1. WHEN the user clicks "Start Processing", THE Application SHALL iterate through all valid image files in the Input_Folder
2. THE Application SHALL display a progress indicator during batch processing
3. FOR each successfully processed form, THE Application SHALL store the results in the internal DataFrame
4. FOR each form that fails alignment or reading, THE Application SHALL log the error and continue with the next form
5. THE Application SHALL maintain a count of successfully processed forms and failed forms

### Requirement 5: Satisfaction Score Calculation

**User Story:** As a QA administrator, I want the application to calculate a Satisfaction Score, so that I can quickly understand overall QA results.

#### Acceptance Criteria

1. THE Analytics_Engine SHALL calculate a Satisfaction_Score for each form using the formula: ((Count_Yes × 100) + (Count_Somewhat × 50) + (Count_No × 0)) / Total_Valid_Questions
2. THE Analytics_Engine SHALL calculate batch-level Satisfaction_Score as the average of all valid forms' scores
3. THE Analytics_Engine SHALL treat Invalid_Form as having 0 Satisfaction_Score in batch calculations
4. THE Application SHALL store all calculated Satisfaction_Score values in the DataFrame

### Requirement 6: Results Storage

**User Story:** As a QA administrator, I want the application to store results in memory, so that I can generate reports without re-processing the images.

#### Acceptance Criteria

1. THE Data_Store SHALL maintain a Pandas DataFrame containing one row per processed form
2. THE Data_Store SHALL store the following columns: Form_ID, Q1-Q14 (Yes/Somewhat/No/Invalid), Form_Score, and Valid flag
3. THE Data_Store SHALL persist the DataFrame in class variables accessible by other components

### Requirement 7: Report Generation and Display

**User Story:** As a QA administrator, I want to view and print an analytics dashboard, so that I can share QA results with stakeholders.

#### Acceptance Criteria

1. THE "View & Print Report" button SHALL remain disabled until batch processing is complete
2. WHEN the user clicks "View & Print Report", THE Analytics_Engine SHALL generate an HTML file containing Plotly visualizations
3. THE Dashboard SHALL include a Stacked Bar Chart showing the count of Yes/Somewhat/No/Invalid for each of the 14 questions
4. THE Dashboard SHALL include a Pie Chart showing the overall distribution of answers across the entire batch
5. THE Dashboard SHALL display the Overall Satisfaction_Score as a large text element
6. THE Application SHALL save the HTML file to a temporary application data folder
7. THE Application SHALL open the HTML file in the user's default web browser using the webbrowser module

### Requirement 8: Error Handling

**User Story:** As a QA administrator, I want the application to handle errors gracefully, so that batch processing continues even if individual forms fail.

#### Acceptance Criteria

1. WHEN a form image cannot be read, THE Application SHALL log the error and mark the form as Invalid in the DataFrame
2. WHEN perspective transform fails, THE Application SHALL log the error and mark the form as Invalid in the DataFrame
3. THE Application SHALL display error summaries to the user after batch processing completes
4. THE GUI SHALL remain responsive during batch processing

### Requirement 9: User Interface

**User Story:** As a QA administrator, I want a modern desktop interface, so that the application is easy to use.

#### Acceptance Criteria

1. THE GUI SHALL be built using CustomTkinter for a modern appearance
2. THE GUI SHALL display the selected Input_Folder path
3. THE GUI SHALL provide a "Browse" button to select the Input_Folder
4. THE GUI SHALL provide a "Start Processing" button to begin batch processing
5. THE GUI SHALL provide a "View & Print Report" button that enables after processing completes
6. THE GUI SHALL display a status/progress message area

### Requirement 10: Application Configuration

**User Story:** As a developer, I want the application to use standardized constants, so that form specifications can be easily adjusted.

#### Acceptance Criteria

1. THE Config class SHALL define FORM_WIDTH as 800 pixels
2. THE Config class SHALL define FORM_HEIGHT as 1000 pixels
3. THE Config class SHALL define CHECKBOX_THRESHOLD as 0.15
4. THE Config class SHALL define ROW_COUNT as 14
5. THE Config class SHALL define COLUMN_COUNT as 3