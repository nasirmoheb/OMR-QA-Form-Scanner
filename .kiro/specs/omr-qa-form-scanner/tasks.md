# Implementation Plan: OMR QA Form Scanner

## Overview

This implementation plan breaks down the OMR QA Form Scanner desktop application into discrete, actionable coding tasks. Each task builds on previous steps and includes specific references to requirements. The application uses Python with CustomTkinter for GUI, OpenCV for image processing, Pandas for data storage, and Plotly for analytics reports.

## Tasks

- [x] 1. Set up project structure and core configuration
  - [x] 1.1 Create project directory structure (src/, tests/, assets/)
  - [x] 1.2 Create Config class with all constants
    - Define FORM_WIDTH, FORM_HEIGHT, CHECKBOX_THRESHOLD, ROW_COUNT, COLUMN_COUNT
    - Define SCORE_YES, SCORE_SOMEWHAT, SCORE_NO weights
    - Define SUPPORTED_EXTENSIONS tuple
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - [x] 1.3 Set up logging configuration
  - [x] 1.4 Configure virtual environment and install dependencies
    - Install: customtkinter, opencv-python, numpy, pandas, plotly
    - _Requirements: 9.1_

- [x] 2. Implement data layer (DataStore)
  - [x] 2.1 Create DataStore class with class-level DataFrame
    - Initialize empty DataFrame with columns: Form_ID, Q1-Q14, Form_Score, Valid
    - _Requirements: 6.1, 6.2_
  - [x] 2.2 Implement add_form_result method
    - Add a form's results to the DataFrame
    - _Requirements: 6.1_
  - [x] 2.3 Implement get_results_dataframe method
    - Return the full results DataFrame
    - _Requirements: 6.3_
  - [x] 2.4 Implement get_valid_forms method
    - Return only valid form results
    - _Requirements: 6.3_
  - [x] 2.5 Implement get_batch_totals method
    - Calculate batch-level totals and statistics
    - _Requirements: 6.3_

- [x] 3. Implement vision processing layer - ImageAligner
  - [x] 3.1 Create ImageAligner class
    - Initialize with configuration
    - _Requirements: 2.1_
  - [x] 3.2 Implement detect_fiducial_markers method
    - Detect 4 corner fiducial markers using OpenCV contour detection
    - Handle cases with <4, =4, and >4 markers
    - _Requirements: 2.1, 2.3, 2.4_
  - [x] 3.3 Implement calculate_perspective_transform method
    - Calculate perspective transform matrix from marker positions
    - _Requirements: 2.2_
  - [x] 3.4 Implement align_image method
    - Apply perspective transform to align image to 800x1000
    - _Requirements: 2.2_

- [x] 4. Implement vision processing layer - CheckboxReader
  - [x] 4.1 Create CheckboxReader class
    - Initialize with threshold configuration
    - _Requirements: 3.3_
  - [x] 4.2 Implement calculate_pixel_density method
    - Calculate ratio of dark pixels in a region
    - Use grayscale conversion and thresholding
    - _Requirements: 3.2, 3.3_
  - [x] 4.3 Implement read_checkbox_grid method
    - Divide aligned image into 14x3 grid
    - Calculate pixel density for each checkbox region
    - _Requirements: 3.1, 3.2_
  - [x] 4.4 Implement determine_selection method
    - Determine which column is selected based on densities
    - Handle 0, 1, or >1 checkboxes above threshold
    - _Requirements: 3.4, 3.5, 3.6_
  - [x] 4.5 Implement coordinate calculation helper
    - Calculate checkbox region boundaries based on grid layout
    - _Requirements: 3.1_

- [x] 5. Implement VisionProcessor (integrates ImageAligner and CheckboxReader)
  - [x] 5.1 Create VisionProcessor class
    - Initialize with ImageAligner and CheckboxReader
    - _Requirements: 2.1_
  - [x] 5.2 Implement process_form method
    - Load image, detect markers, align, read checkboxes
    - Return form results dictionary
    - _Requirements: 2.1, 2.2, 3.1, 3.4_
  - [x] 5.3 Implement validate_form_count method
    - Check if image can be processed
    - _Requirements: 2.3_

- [x] 6. Implement analytics layer - AnalyticsEngine
  - [x] 6.1 Create AnalyticsEngine class
    - Initialize with DataStore reference
    - _Requirements: 5.1_
  - [x] 6.2 Implement calculate_form_score method
    - Calculate: ((Yes × 100) + (Somewhat × 50) + (No × 0)) / Total_Valid_Questions
    - _Requirements: 5.1_
    - **Property 1: Form Score Calculation** - _Validates: Requirements 5.1_
  - [x] 6.3 Implement calculate_batch_score method
    - Calculate average of all valid forms' Form_Score
    - Invalid forms count as 0
    - _Requirements: 5.2, 5.3_
    - **Property 2: Batch Score Calculation** - _Validates: Requirements 5.2_
  - [x] 6.4 Implement generate_report method
    - Generate Plotly HTML dashboard
    - _Requirements: 7.2, 7.6_

- [x] 7. Implement analytics layer - PlotlyGenerator
  - [x] 7.1 Create PlotlyGenerator class
    - _Requirements: 7.3, 7.4, 7.5_
  - [x] 7.2 Implement create_stacked_bar_chart method
    - Show count of Yes/Somewhat/No/Invalid for each question
    - _Requirements: 7.3_
  - [x] 7.3 Implement create_pie_chart method
    - Show overall answer distribution
    - _Requirements: 7.4_
  - [x] 7.4 Implement create_score_display method
    - Display Overall Satisfaction Score as large text
    - _Requirements: 7.5_
  - [x] 7.5 Implement generate_dashboard_html method
    - Combine all charts into complete HTML dashboard
    - _Requirements: 7.2, 7.6_

- [x] 8. Checkpoint - Verify data and analytics components
  - Ensure all data layer and analytics tests pass
  - Ask the user if questions arise
  - **Property 3: DataFrame Column Integrity** - _Validates: Requirements 6.2_
  - **Property 4: Checkbox Threshold Classification** - _Validates: Requirements 3.3_
  - **Property 5: Single Selection Per Row** - _Validates: Requirements 3.5, 3.6_
  - **Property 6: Invalid Form Score** - _Validates: Requirements 5.3_

- [x] 9. Implement GUI layer - OMRGUI
  - [x] 9.1 Create OMRGUI class
    - Initialize main window with CustomTkinter
    - Set window title and dimensions
    - _Requirements: 9.1_
  - [x] 9.2 Implement create_widgets method
    - Create folder path display label
    - Create "Browse" button
    - Create "Start Processing" button
    - Create "View & Print Report" button (initially disabled)
    - Create status message area
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_
  - [x] 9.3 Implement select_input_folder method
    - Open folder selection dialog
    - Validate folder exists
    - Display selected path
    - _Requirements: 1.1, 1.2_
  - [x] 9.4 Implement scan_input_folder method
    - Scan for .jpg and .png files
    - Display count of identified images
    - _Requirements: 1.3, 1.4_
  - [x] 9.5 Implement start_processing method
    - Initialize DataStore
    - Iterate through all image files
    - Process each form using VisionProcessor
    - Store results in DataStore
    - Track success/failure counts
    - Enable "View & Print Report" button on completion
    - Display progress and error summary
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.1, 8.2, 8.3, 8.4_
  - [x] 9.6 Implement view_report method
    - Generate Plotly HTML dashboard
    - Save to temporary folder
    - Open in default web browser
    - _Requirements: 7.1, 7.2, 7.6, 7.7_
  - [x] 9.7 Implement update_status method
    - Update status message display
    - _Requirements: 9.6_
  - [x] 9.8 Implement run method
    - Start the GUI main loop
    - _Requirements: 9.1_

- [x] 10. Create main application entry point
  - [x] 10.1 Create main.py
    - Import all modules
    - Create and run OMRGUI instance
    - _Requirements: 9.1_

- [x] 11. Checkpoint - Verify GUI and full integration
  - Ensure all GUI components render correctly
  - Test folder selection flow
  - Test processing flow with sample images
  - Ask the user if questions arise

- [x] 12. Final verification and testing
  - [x] 12.1 Run full application test
    - Test complete workflow: select folder → process → view report
  - [x] 12.2 Verify error handling
    - Test with invalid folder
    - Test with corrupted images
    - _Requirements: 8.1, 8.2, 8.3_
  - [x] 12.3 Verify report generation
    - Check HTML output contains all required charts
    - _Requirements: 7.3, 7.4, 7.5_

## Notes

- All property tests validate correctness properties defined in the design document
- Checkpoints ensure incremental validation of the implementation
- The application follows a clean separation of concerns: GUI → Vision/Processing → Data → Analytics
- Error handling ensures batch processing continues even if individual forms fail

## Dependencies

```
customtkinter>=5.0.0
opencv-python>=4.8.0
numpy>=1.24.0
pandas>=2.0.0
plotly>=5.18.0
hypothesis>=6.0.0  # For property-based tests
pytest>=7.0.0      # For unit tests
```