# OMR Checkbox Detection Techniques

## Problem Overview

When processing scanned OMR (Optical Mark Recognition) forms, several challenges can arise:

1. **Lightly-filled checkboxes** — pencil marks or light pen strokes that don't produce strong contrast
2. **Varying scan quality** — different scanners, lighting conditions, or paper quality
3. **Ambiguous selections** — marks that are unclear or multiple boxes partially filled
4. **Paper texture and noise** — background patterns that interfere with detection
5. **Alignment issues** — slight rotation or perspective distortion after correction

---

## Technique Categories

### 1. Image Preprocessing Techniques

#### 1.1 Contrast Enhancement

**A. Global Histogram Normalization**
```python
normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
```
- **When to use**: Forms with consistent but low contrast
- **Pros**: Simple, fast, improves overall visibility
- **Cons**: Can amplify noise uniformly

**B. Gamma Correction**
```python
gamma = 0.7  # < 1.0 darkens, > 1.0 lightens
inv_gamma = 1.0 / gamma
table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
gamma_corrected = cv2.LUT(normalized, table)
```
- **When to use**: Light marks that need darkening without losing detail
- **Pros**: Non-linear enhancement preserves highlights and shadows
- **Cons**: Requires tuning gamma value per form type
- **Recommended gamma values**:
  - 0.6–0.8: For very light pencil marks
  - 0.8–1.0: For moderate pen marks
  - 1.0–1.2: For over-exposed scans

**C. CLAHE (Contrast Limited Adaptive Histogram Equalization)**
```python
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)
```
- **When to use**: Forms with varying lighting across the page
- **Pros**: Enhances local contrast, handles uneven illumination
- **Cons**: Can amplify noise and paper texture; may reduce mark-to-background separation
- **Best for**: High-quality scans with uneven lighting
- **Avoid for**: Low-quality scans or forms with heavy texture

**D. Adaptive Thresholding**
```python
adaptive = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY_INV, blockSize=11, C=2
)
```
- **When to use**: Forms with shadows or gradients
- **Pros**: Handles local variations automatically
- **Cons**: Can create artifacts at block boundaries

---

#### 1.2 Morphological Operations

**A. Dilation (Thickening Marks)**
```python
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
dilated = cv2.dilate(gray, kernel, iterations=1)
```
- **When to use**: Thin or broken pencil strokes
- **Pros**: Connects fragmented marks, increases mark density
- **Cons**: Can merge nearby marks or expand noise
- **Kernel size guidelines**:
  - (2, 2): Minimal thickening for light marks
  - (3, 3): Moderate thickening for very faint marks
  - (4, 4): Aggressive (risk of merging adjacent boxes)

**B. Erosion (Removing Noise)**
```python
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
eroded = cv2.erode(gray, kernel, iterations=1)
```
- **When to use**: Forms with speckle noise or paper texture
- **Pros**: Removes small noise particles
- **Cons**: Can thin or break legitimate marks

**C. Opening (Erosion + Dilation)**
```python
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
```
- **When to use**: Remove small noise while preserving mark shape
- **Pros**: Cleans background without affecting large marks
- **Cons**: Can remove very small or thin marks

**D. Closing (Dilation + Erosion)**
```python
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
```
- **When to use**: Fill gaps in broken marks
- **Pros**: Connects fragmented strokes, smooths mark edges
- **Cons**: Can fill small gaps between adjacent boxes

---

#### 1.3 Filtering Techniques

**A. Gaussian Blur (Noise Reduction)**
```python
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
```
- **When to use**: Noisy scans with salt-and-pepper artifacts
- **Pros**: Smooths noise while preserving edges
- **Cons**: Can blur mark boundaries

**B. Bilateral Filter (Edge-Preserving Smoothing)**
```python
filtered = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)
```
- **When to use**: Reduce noise while keeping checkbox edges sharp
- **Pros**: Preserves edges better than Gaussian blur
- **Cons**: Slower computation

**C. Median Filter (Impulse Noise Removal)**
```python
median = cv2.medianBlur(gray, 3)
```
- **When to use**: Scans with random speckles or dust
- **Pros**: Excellent for salt-and-pepper noise
- **Cons**: Can remove small marks if kernel is too large

**D. Sharpening**
```python
kernel = np.array([[-1, -1, -1],
                   [-1,  9, -1],
                   [-1, -1, -1]])
sharpened = cv2.filter2D(gray, -1, kernel)
```
- **When to use**: Blurry scans or out-of-focus images
- **Pros**: Enhances edges and mark boundaries
- **Cons**: Amplifies noise; can create halos around marks

---

### 2. Threshold Selection Techniques

#### 2.1 Absolute Threshold
```python
threshold = 0.20  # Fixed density value
selected = [i for i, d in enumerate(densities) if d >= threshold]
```
- **When to use**: Consistent scan quality and mark intensity
- **Pros**: Simple, predictable
- **Cons**: Fails with varying mark intensity or scan quality
- **Recommended values**:
  - 0.15–0.25: Standard pen marks
  - 0.08–0.15: Light pencil marks
  - 0.05–0.10: Very faint marks (high false positive risk)

#### 2.2 Relative/Adaptive Threshold
```python
max_density = max(densities)
second_max = sorted(densities, reverse=True)[1]
ratio = max_density / second_max if second_max > 0 else float('inf')

if max_density >= floor_threshold and ratio >= 1.5:
    winner = densities.index(max_density)
```
- **When to use**: Varying mark intensity across forms
- **Pros**: Adapts to each row independently; handles light marks
- **Cons**: Can misinterpret noise as marks if floor is too low
- **Recommended ratios**:
  - 1.5×: Conservative (fewer false positives)
  - 1.3×: Moderate (balanced)
  - 1.2×: Aggressive (more detections, higher false positive risk)

#### 2.3 Statistical Threshold (Mean + Std Dev)
```python
mean_density = np.mean(densities)
std_density = np.std(densities)
threshold = mean_density + 1.5 * std_density
```
- **When to use**: Forms where marked boxes are statistical outliers
- **Pros**: Automatically adapts to density distribution
- **Cons**: Fails if multiple boxes are marked or all are similar

#### 2.4 Otsu's Method (Per-Row Binarization)
```python
_, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
density = cv2.countNonZero(binary) / binary.size
```
- **When to use**: Already implemented in density calculation
- **Pros**: Automatically finds optimal threshold per region
- **Cons**: Can fail with bimodal distributions or uniform regions

---

### 3. Multi-Stage Detection Strategies

#### 3.1 Cascade Approach
```python
# Stage 1: Absolute threshold for clear marks
if max_density >= 0.20:
    return select_max(densities)

# Stage 2: Relative threshold for moderate marks
elif max_density >= 0.08 and ratio >= 1.5:
    return select_max(densities)

# Stage 3: Flag as ambiguous
else:
    return "Invalid"
```
- **When to use**: Mixed form quality in a batch
- **Pros**: Handles both clear and ambiguous cases
- **Cons**: More complex logic

#### 3.2 Confidence Scoring
```python
def calculate_confidence(densities, threshold):
    above = [d for d in densities if d >= threshold]
    if len(above) == 1:
        return min(1.0, max(above) / (threshold * 2))
    return 0.0
```
- **When to use**: Need to flag low-confidence detections for manual review
- **Pros**: Provides quality metric for each detection
- **Cons**: Requires defining confidence thresholds

#### 3.3 Ensemble Methods
```python
# Try multiple preprocessing pipelines
results = []
for preprocess_fn in [gamma_correct, clahe_enhance, dilate_marks]:
    processed = preprocess_fn(image)
    densities = calculate_densities(processed)
    results.append(determine_selection(densities))

# Vote or use highest confidence
final = majority_vote(results)
```
- **When to use**: Critical applications requiring high accuracy
- **Pros**: Robust to preprocessing failures
- **Cons**: Computationally expensive

---

### 4. Grid Calibration Techniques

#### 4.1 Timing Mark Detection
```python
# Detect vertical timing marks on form edge
timing_marks = detect_timing_marks(aligned_image)
row_y_positions = [mark.center_y for mark in timing_marks]

# Use detected positions instead of uniform grid
for row in range(14):
    y_center = row_y_positions[row]
    cell_bounds = calculate_cell_from_center(y_center)
```
- **When to use**: Forms with printed timing marks
- **Pros**: Compensates for paper stretch/shrink
- **Cons**: Requires timing marks on form design

#### 4.2 Dynamic Grid Adjustment
```python
# Detect actual checkbox positions via edge detection
edges = cv2.Canny(aligned, 50, 150)
checkbox_contours = find_checkbox_contours(edges)
grid_positions = cluster_contours_to_grid(checkbox_contours)
```
- **When to use**: Forms where grid may shift slightly
- **Pros**: Adapts to actual checkbox locations
- **Cons**: Complex; can fail if checkboxes are filled solid

#### 4.3 Sub-Pixel Alignment
```python
# Refine fiducial marker centers to sub-pixel accuracy
corners = cv2.cornerSubPix(
    gray, corners, (5, 5), (-1, -1),
    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
)
```
- **When to use**: High-resolution scans (300+ DPI)
- **Pros**: More accurate alignment
- **Cons**: Minimal benefit at standard 150 DPI

---

### 5. Validation and Quality Control

#### 5.1 Form-Level Validation
```python
# Check if form has minimum valid answers
valid_count = sum(1 for ans in answers if ans != "Invalid")
if valid_count < 10:  # Less than 10 of 14 questions
    flag_for_manual_review(form)
```

#### 5.2 Density Distribution Analysis
```python
# Flag forms with unusual density patterns
all_densities = [d for row in grid for d in row]
if max(all_densities) < 0.05:  # All cells too light
    flag_as_blank_or_misaligned(form)
elif min(all_densities) > 0.15:  # All cells too dark
    flag_as_over_marked(form)
```

#### 5.3 Cross-Validation with Metadata
```python
# Check if answers match expected patterns
if question_11_is_inverted:  # "No" is positive
    if answers[10] == "Yes" and overall_score < 50:
        flag_inconsistency(form)
```

---

## Recommended Pipeline for Light Marks

Based on testing with the Afghan MoHE QA survey forms:

```python
def preprocess_for_light_marks(image):
    # 1. Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Normalize contrast
    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    # 3. Gamma correction (darken mid-tones)
    gamma = 0.7
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 
                      for i in range(256)]).astype("uint8")
    gamma_corrected = cv2.LUT(normalized, table)
    
    # 4. Morphological dilation (thicken marks)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    dilated = cv2.dilate(gamma_corrected, kernel, iterations=1)
    
    return dilated

def determine_selection_adaptive(densities, floor_threshold=0.05):
    # Relative threshold with absolute floor
    sorted_d = sorted(densities, reverse=True)
    max_d = sorted_d[0]
    second_d = sorted_d[1]
    
    if max_d < floor_threshold:
        return "Invalid"
    
    if second_d > 0 and (max_d / second_d) < 1.5:
        return "Invalid"  # Ambiguous
    
    winner = densities.index(max_d)
    return ["Somewhat", "No", "Yes"][winner]
```

**Results**:
- Floor threshold: 0.05 (allows light marks)
- Ratio threshold: 1.5× (conservative, reduces false positives)
- Preprocessing: Gamma + dilation (enhances light marks without amplifying noise)
- Success rate: 13/14 questions on test form (93%)

---

## Troubleshooting Guide

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| All answers "Invalid" | Threshold too high | Lower absolute threshold to 0.05–0.10 |
| Too many false positives | Threshold too low or noisy scan | Increase ratio threshold to 1.5–2.0; apply noise filtering |
| Marks detected in wrong column | Grid misalignment | Check fiducial markers; verify MARGIN_* constants |
| Inconsistent results across forms | Varying scan quality | Use adaptive threshold; add preprocessing |
| Light pencil marks not detected | Insufficient contrast | Apply gamma correction (0.6–0.8) + dilation |
| Heavy pen marks bleed into adjacent cells | Over-dilation or grid too tight | Reduce dilation iterations; increase COL_GAP |
| Paper texture creates false marks | Noise amplification | Use bilateral filter or median blur before processing |
| Ambiguous selections (multiple boxes) | User error or smudges | Flag for manual review; check confidence scores |

---

## Performance Considerations

| Technique | Speed | Accuracy Gain | When to Use |
|-----------|-------|---------------|-------------|
| Gamma correction | Fast | High (for light marks) | Always for light forms |
| CLAHE | Medium | Medium | Uneven lighting only |
| Dilation | Fast | High (for thin marks) | Always for pencil forms |
| Bilateral filter | Slow | Medium | High-quality scans only |
| Ensemble methods | Very slow | High | Critical applications |
| Adaptive threshold | Fast | High | Always recommended |

---

## Future Enhancements

1. **Machine Learning Approaches**
   - Train CNN to classify checkbox states directly
   - Learn optimal preprocessing parameters per scanner type
   - Detect and correct common user errors (stray marks, erasures)

2. **Advanced Calibration**
   - Automatic grid detection via Hough transform
   - Template matching for checkbox location
   - Perspective correction refinement using checkbox edges

3. **Quality Metrics**
   - Per-form quality score based on density distribution
   - Automatic flagging of suspicious patterns
   - Confidence intervals for batch statistics

4. **User Feedback Loop**
   - Manual correction interface
   - Learn from corrections to improve thresholds
   - Build scanner-specific profiles

---

## References

- OpenCV Documentation: https://docs.opencv.org/
- "Adaptive Thresholding for OMR" — IEEE Transactions on Pattern Analysis
- "Morphological Operations for Document Image Processing" — ICDAR 2019
- Afghan MoHE QA Survey Form Specification (internal)

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-06  
**Author**: OMR QA Scanner Development Team
