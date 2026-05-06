# Design Document: OMR QA Form Scanner

## Overview

This design document specifies the architecture and implementation details for the OMR QA Form Scanner desktop application. The application is a purely offline desktop tool that performs batch Optical Mark Recognition on scanned QA forms, stores aggregated results in memory, and generates interactive Plotly HTML analytics reports.

### System Goals

1. **Batch Processing**: Process multiple scanned form images automatically from a user-selected folder
2. **Image Alignment**: Use fiducial markers to align skewed/scanned forms to a standardized template
3. **Checkbox Detection**: Extract checkbox selections using pixel density analysis
4. **Analytics**: Generate interactive Plotly dashboards with aggregated results
5. **Offline Operation**: All processing occurs locally without network connectivity

### Key Characteristics

- Purely offline desktop application
- Object-Oriented architecture with complete separation of concerns
- Robust error handling for graceful degradation during batch processing
- Modern CustomTkinter-based GUI

---

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph GUI["GUI Layer"]
        GUI[OMRGUI Window]
    end
    
    subgraph Vision["Vision/Processing Layer"]
        VP[VisionProcessor]
        IP[ImageAligner]
        CR[CheckboxReader]
    end
    
    subgraph Analytics["Analytics Layer"]
        AE[AnalyticsEngine]
        PG[PlotlyGenerator]
    end
    
    subgraph Data["Data Layer"]
        DS[DataStore]
        DF[Pandas DataFrame]
    end
    
    GUI -->|Triggers| VP
    VP -->|Reads Images| DS
    DS -->|Stores Results| DF
    AE -->|Reads Data| DF
    AE -->|Generates| PG
    PG -->|Opens| Browser
```

### Layer Responsibilities

1. **GUI Layer**: User interface built with CustomTkinter, handles user interactions and displays status
2. **Vision/Processing Layer**: OpenCV-based image alignment and checkbox detection
3. **Analytics Layer**: Plotly-based dashboard generation and report creation
4. **Data Layer**: Pandas-based in-memory data storage and aggregation

---

## Components and Interfaces

### Class: Config

Centralized configuration class defining all application constants.

```python
class Config:
    """Application configuration constants."""
    
    # Form dimensions (pixels) — A4 portrait at 150 DPI (210 × 297 mm)
    FORM_WIDTH: int = 1240
    FORM_HEIGHT: int = 1754
    
    # Checkbox detection threshold (15% dark pixels)
    CHECKBOX_THRESHOLD: float = 0.15
    
    # Grid dimensions
    ROW_COUNT: int = 14
    COLUMN_COUNT: int = 3
    
    # Score weights
    SCORE_YES: int = 100
    SCORE_SOMEWHAT: int = 50
    SCORE_NO: int = 0
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS: tuple = ('.jpg', '.jpeg', '.png')
    
    # Checkbox region dimensions (relative to aligned form)
    CHECKBOX_WIDTH: int = 80
    CHECKBOX_HEIGHT: int = 40
    
    # Fiducial marker expected size (pixels)
    MARKER_SIZE: int = 30
```

### Class: VisionProcessor

Main class for image processing and OMR detection.

```python
class VisionProcessor:
    """Handles image alignment and checkbox reading."""
    
    def __init__(self) -> None:
        """Initialize the vision processor."""
        self._image_aligner = ImageAligner()
        self._checkbox_reader = CheckboxReader()
    
    def process_form(self, image_path: str) -> dict:
        """
        Process a single form image.
        
        Args:
            image_path: Path to the form image file
            
        Returns:
            Dictionary containing form results
        """
        # 1. Load image
        # 2. Detect fiducial markers
        # 3. Apply perspective transform
        # 4. Read checkboxes
        # 5. Calculate form score
        pass
    
    def validate_form_count(self, image_path: str) -> bool:
        """Check if image can be processed."""
        pass
```

### Class: ImageAligner

Handles fiducial marker detection and perspective transformation.

```python
class ImageAligner:
    """Handles form image alignment using fiducial markers."""
    
    def detect_fiducial_markers(self, image: np.ndarray) -> list:
        """
        Detect the four corner fiducial markers.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of 4 (x, y) tuples representing marker positions
        """
        pass
    
    def calculate_perspective_transform(self, markers: list) -> np.ndarray:
        """
        Calculate perspective transform matrix.
        
        Args:
            markers: List of 4 marker positions
            
        Returns:
            3x3 transformation matrix
        """
        pass
    
    def align_image(self, image: np.ndarray, transform_matrix: np.ndarray) -> np.ndarray:
        """
        Apply perspective transform to align image.
        
        Args:
            image: Input image
            transform_matrix: Perspective transform matrix
            
        Returns:
            Aligned image
        """
        pass
```

### Class: CheckboxReader

Handles checkbox region detection and pixel density analysis.

```python
class CheckboxReader:
    """Reads checkbox selections from aligned form images."""
    
    def __init__(self) -> None:
        """Initialize with configuration."""
        self._threshold = Config.CHECKBOX_THRESHOLD
    
    def calculate_pixel_density(self, region: np.ndarray) -> float:
        """
        Calculate the ratio of dark pixels in a region.
        
        Args:
            region: Image region as numpy array
            
        Returns:
            Ratio of dark pixels (0.0 to 1.0)
        """
        pass
    
    def read_checkbox_grid(self, aligned_image: np.ndarray) -> list:
        """
        Read all checkboxes from aligned form.
        
        Args:
            aligned_image: Aligned form image
            
        Returns:
            List of 14 items, each containing column selection
        """
        pass
    
    def determine_selection(self, densities: list) -> str:
        """
        Determine which column is selected based on densities.
        
        Args:
            densities: List of 3 density values
            
        Returns:
            'Yes', 'Somewhat', 'No', or 'Invalid'
        """
        pass
```

### Class: DataStore

Manages in-memory data storage using Pandas.

```python
class DataStore:
    """Manages form data storage using Pandas DataFrame."""
    
    # Class-level DataFrame storage
    _results_df: pd.DataFrame = None
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize empty DataFrame with required columns."""
        pass
    
    @classmethod
    def add_form_result(cls, form_id: str, results: dict) -> None:
        """
        Add a form result to the DataFrame.
        
        Args:
            form_id: Unique identifier for the form
            results: Dictionary with Q1-Q14 results and scores
        """
        pass
    
    @classmethod
    def get_results_dataframe(cls) -> pd.DataFrame:
        """Get the results DataFrame."""
        pass
    
    @classmethod
    def get_valid_forms(cls) -> pd.DataFrame:
        """Get only valid form results."""
        pass
    
    @classmethod
    def get_batch_totals(cls) -> dict:
        """Calculate batch-level totals and statistics."""
        pass
```

### Class: AnalyticsEngine

Handles score calculations and dashboard generation.

```python
class AnalyticsEngine:
    """Handles analytics calculations and report generation."""
    
    def calculate_form_score(self, form_results: dict) -> float:
        """
        Calculate satisfaction score for a single form.
        
        Args:
            form_results: Dictionary with Q1-Q14 results
            
        Returns:
            Score from 0 to 100
        """
        pass
    
    def calculate_batch_score(self) -> float:
        """Calculate average batch satisfaction score."""
        pass
    
    def generate_report(self, output_path: str) -> str:
        """
        Generate Plotly HTML dashboard.
        
        Args:
            output_path: Path to save HTML file
            
        Returns:
            Path to generated HTML file
        """
        pass
```

### Class: PlotlyGenerator

Generates Plotly visualizations for the dashboard.

```python
class PlotlyGenerator:
    """Generates Plotly chart objects for the dashboard."""
    
    def create_stacked_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create stacked bar chart for question breakdown."""
        pass
    
    def create_pie_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create pie chart for answer distribution."""
        pass
    
    def create_score_display(self, score: float) -> str:
        """Create HTML string for score display."""
        pass
    
    def generate_dashboard_html(self, figures: list, score: float) -> str:
        """Generate complete HTML dashboard."""
        pass
```

### Class: OMRGUI

Main GUI window using CustomTkinter.

```python
class OMRGUI:
    """Main application GUI window."""
    
    def __init__(self) -> None:
        """Initialize the GUI window and components."""
        pass
    
    def create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        pass
    
    def select_input_folder(self) -> None:
        """Handle folder selection dialog."""
        pass
    
    def start_processing(self) -> None:
        """Handle start processing button click."""
        pass
    
    def view_report(self) -> None:
        """Handle view report button click."""
        pass
    
    def update_status(self, message: str) -> None:
        """Update status message display."""
        pass
    
    def run(self) -> None:
        """Start the GUI main loop."""
        pass
```

---

## Data Models

### Form Result Structure

```python
@dataclass
class FormResult:
    """Data model for a single form's results."""
    
    form_id: str              # Unique identifier (filename)
    q1: str                   # Q1 answer: 'Yes', 'Somewhat', 'No', 'Invalid'
    q2: str                   # Q2 answer
    # ... (q3 through q14)
    q14: str                  # Q14 answer
    form_score: float         # Individual form satisfaction score
    is_valid: bool            # Whether form was processed successfully
    
# DataFrame columns:
# ['Form_ID', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 
#  'Q9', 'Q10', 'Q11', 'Q12', 'Q13', 'Q14', 'Form_Score', 'Valid']
```

### Dashboard Data Structure

```python
@dataclass
class DashboardData:
    """Data model for dashboard visualizations."""
    
    question_counts: dict     # {q_num: {'Yes': count, 'No': count, 'Somewhat': count, 'Invalid': count}}
    total_responses: int      # Total valid responses across all questions
    answer_distribution: dict # {'Yes': count, 'No': count, 'Somewhat': count, 'Invalid': count}
    batch_score: float        # Overall batch satisfaction score
    valid_forms_count: int    # Number of successfully processed forms
    failed_forms_count: int   # Number of failed forms
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The application involves computer vision processing (OpenCV), which is complex but has testable properties. Key testable areas include:
- Score calculations (pure functions)
- Data aggregation logic
- Checkbox reading logic (with mock images)
- Round-trip data integrity

### Property 1: Form Score Calculation

*For any* valid form result with a known distribution of Yes/Somewhat/No answers, the calculated Form_Score SHALL equal ((Yes × 100) + (Somewhat × 50) + (No × 0)) / Total_Valid_Questions

**Validates: Requirements 5.1**

### Property 2: Batch Score Calculation

*For any* batch of form results, the batch Satisfaction_Score SHALL equal the average of all valid forms' Form_Score values

**Validates: Requirements 5.2**

### Property 3: DataFrame Column Integrity

*For any* processed form added to the DataStore, the DataFrame SHALL contain exactly 17 columns: Form_ID, Q1-Q14, Form_Score, and Valid

**Validates: Requirements 6.2**

### Property 4: Checkbox Threshold Classification

*For any* checkbox region with pixel density >= 0.15, the system SHALL classify it as "marked", and for any region with density < 0.15, it SHALL be classified as "unmarked"

**Validates: Requirements 3.3**

### Property 5: Single Selection Per Row

*For any* question row in a processed form, the system SHALL classify the result as "Invalid" when zero OR more than one checkbox columns have density above the threshold

**Validates: Requirements 3.5, 3.6**

### Property 6: Invalid Form Score

*For any* form marked as invalid (is_valid = False), the Form_Score SHALL be 0

**Validates: Requirements 5.3**

---

## Error Handling

### Error Categories

1. **File Access Errors**: Missing folder, unreadable images
2. **Alignment Errors**: Fewer than 4 fiducial markers detected
3. **Processing Errors**: Image corruption, unexpected format
4. **Generation Errors**: Plotly dashboard creation failure

### Error Handling Strategy

| Error Type | Handling Approach | User Feedback |
|------------|------------------|---------------|
| Invalid folder path | Validate before processing | Error message in status area |
| Corrupted image file | Skip form, log error | Show failed form count after processing |
| Failed marker detection | Mark form as Invalid | Show warning, continue batch |
| Perspective transform failure | Mark form as Invalid | Show warning, continue batch |
| Dashboard generation failure | Show error dialog | Display error message |

### Error Logging

- All errors are logged to a list accessible for display
- Failed form IDs are tracked for user reference
- Processing continues to next form on error (fail-fast is NOT used)

---

## Testing Strategy

### Testing Approach

This application requires a **dual testing approach** combining unit tests and property-based tests:

**Unit Tests**: 
- Specific examples of form processing
- Edge cases for checkbox detection threshold
- Error handling scenarios

**Property Tests**:
- Score calculation across various input distributions
- DataFrame structure integrity
- Threshold classification consistency

### Property-Based Testing Configuration

When implementing property-based tests:

- Use **Hypothesis** library for Python
- Minimum 100 iterations per property
- Reference design properties with tag: `Feature: omr-qa-form-scanner, Property N: <description>`

### Test Categories

1. **Unit Tests** (example-based):
   - Test VisionProcessor with sample images
   - Test score calculation with known inputs
   - Test GUI button state transitions

2. **Property Tests**:
   - Test score calculation formula holds for all valid input distributions
   - Test DataFrame column consistency after multiple additions
   - Test threshold classification is consistent across different image regions

3. **Integration Tests**:
   - End-to-end form processing workflow
   - Dashboard generation and browser opening

### Library Selection

| Test Type | Library | Justification |
|-----------|---------|---------------|
| Unit Tests | pytest | Standard Python testing |
| Property Tests | Hypothesis | Robust PBT for Python |

---

## Acceptance Criteria Testing Prework

### Prework Analysis

**1.1. THE Application SHALL provide a folder selection mechanism allowing the user to browse and select an Input_Folder**
- Thoughts: This is a UI interaction - testing that folder dialog opens and returns a path
- Classification: EXAMPLE
- Test Strategy: Verify folder dialog returns valid path, path is displayed in GUI

**1.2. THE Application SHALL validate that the selected folder exists and is accessible**
- Thoughts: This is validation logic - test with valid/invalid paths
- Classification: EXAMPLE
- Test Strategy: Test with existing and non-existing paths

**1.3. THE Application SHALL scan the selected folder and identify all files with .jpg or .png extensions**
- Thoughts: This is file system logic - can generate test files with various extensions
- Classification: PROPERTY
- Test Strategy: Generate folder with various file types, verify only .jpg/.png are selected

**1.4. THE Application SHALL display the count of identified form images to the user before processing begins**
- Thoughts: This is UI display - verify count is shown
- Classification: EXAMPLE
- Test Strategy: Test with known number of image files

**2.1. THE Vision_Processor SHALL detect exactly 4 fiducial markers in each form image**
- Thoughts: This requires actual image processing - we can test marker detection algorithm with synthetic images
- Classification: PROPERTY
- Test Strategy: Generate images with known marker positions, verify detection

**2.2. WHEN 4 fiducial markers are detected, THE Vision_Processor SHALL calculate a perspective transform matrix**
- Thoughts: This is a deterministic mathematical transformation
- Classification: EXAMPLE
- Test Strategy: Test with known marker positions

**2.3. WHEN fewer than 4 fiducial markers are detected, THE Vision_Processor SHALL flag the form as Invalid_Form**
- Thoughts: This is error handling logic - test with various marker counts
- Classification: EXAMPLE
- Test Strategy: Test with 0-3 markers detected

**2.4. WHEN more than 4 fiducial markers are detected, THE Vision_Processor SHALL select the 4 markers that form the largest rectangular area**
- Thoughts: This is a selection algorithm - we can test the logic
- Classification: EXAMPLE
- Test Strategy: Test with 5+ markers

**3.1. THE Vision_Processor SHALL divide the aligned image into a grid of 14 rows and 3 columns**
- Thoughts: This is coordinate calculation - test with known image dimensions
- Classification: EXAMPLE
- Test Strategy: Test grid division calculations

**3.2. FOR each checkbox region, THE Vision_Processor SHALL calculate the pixel density of dark pixels**
- Thoughts: This is a pure function that can be tested with various regions
- Classification: PROPERTY
- Test Strategy: Generate regions with known pixel patterns, verify density calculation

**3.3. THE Vision_Processor SHALL use a threshold of 0.15 to determine if a checkbox is marked**
- Thoughts: This is threshold classification - test boundary conditions
- Classification: PROPERTY
- Test Strategy: Test with densities at exactly 0.15, just below, and just above

**3.4-3.6. Question row selection logic**
- Thoughts: These test the selection algorithm which is testable
- Classification: PROPERTY
- Test Strategy: Test with various density combinations

**4.1-4.5. Batch processing**
- Thoughts: This is integration testing - verify progress updates and storage
- Classification: INTEGRATION
- Test Strategy: Process small batch of test images, verify results

**5.1-5.4. Satisfaction Score Calculation**
- Thoughts: These are pure calculation functions - highly testable with PBT
- Classification: PROPERTY
- Test Strategy: Generate random distributions, verify formula output

**6.1-6.3. Results Storage**
- Thoughts: This tests DataFrame structure - can verify with PBT
- Classification: PROPERTY
- Test Strategy: Add multiple forms, verify DataFrame structure

**7.1-7.7. Report Generation**
- Thoughts: This is integration with Plotly - test HTML output structure
- Classification: INTEGRATION
- Test Strategy: Generate report, verify HTML contains required charts

**8.1-8.4. Error Handling**
- Thoughts: These test error paths - use example-based testing
- Classification: EXAMPLE
- Test Strategy: Test with invalid inputs, verify error handling

**9.1-9.6. User Interface**
- Thoughts: These are UI tests - verify widget states
- Classification: INTEGRATION
- Test Strategy: Test widget creation and state transitions

**10.1-10.5. Application Configuration**
- Thoughts: This is simple value testing
- Classification: SMOKE
- Test Strategy: Verify Config class has correct values

### Property Reflection

After reviewing the prework, the following properties are identified as testable:

1. **File Extension Filtering**: Filtering for .jpg/.png across various inputs - unique value
2. **Pixel Density Calculation**: Pure function for density - unique value
3. **Threshold Classification**: Boundary testing - can be combined with density calculation
4. **Score Calculation**: Formula-based - unique value
5. **Batch Score Calculation**: Average calculation - unique value
6. **DataFrame Structure**: Column consistency - unique value
7. **Question Row Selection**: Multiple density inputs - unique value

**Redundancy Analysis**:
- Properties 3 (Threshold) and 7 (Row Selection) can be combined - both test checkbox detection
- Properties 5 (Score) and 6 (Batch Score) are separate as they test different calculations
- No other significant redundancy found

**Final Property List** (after reflection):
1. Form Score Calculation
2. Batch Score Calculation
3. DataFrame Column Integrity
4. Checkbox Threshold Classification
5. Single Selection Per Row
6. Invalid Form Score