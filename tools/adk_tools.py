import logging
from typing import Dict, List, Any
from google.adk.tools.function_tool import FunctionTool

logger = logging.getLogger(__name__)

# Computational Geometry Helpers for Route-Intersection checks
def _on_segment(p, q, r):
    if (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
        q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1])):
        return True
    return False

def _orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0
    return 1 if val > 0 else 2

def _do_intersect(p1, q1, p2, q2):
    o1 = _orientation(p1, q1, p2)
    o2 = _orientation(p1, q1, q2)
    o3 = _orientation(p2, q2, p1)
    o4 = _orientation(p2, q2, q1)

    if (o1 != o2 and o3 != o4):
        return True

    if (o1 == 0 and _on_segment(p1, p2, q1)): return True
    if (o2 == 0 and _on_segment(p1, q2, q1)): return True
    if (o3 == 0 and _on_segment(p2, p1, q2)): return True
    if (o4 == 0 and _on_segment(p2, q1, q2)): return True

    return False

# Custom ADK tool decorator definition
def adk_tool(name: str):
    def decorator(func):
        func.__name__ = name
        return func
    return decorator

@adk_tool(name="validate_euclidean_distance")
def validate_multimodal_geometry_func(vision_proposal: Any, is_stress_test: bool = False, skip_word_count: bool = False) -> Dict[str, Any]:
    """
    Validates model-proposed spatial telemetry and coordinates.
    Performs Euclidean distance checks and structural word-count audits.
    
    Args:
        vision_proposal: The proposed script and labels from the vision agent.
        is_stress_test: Whether to use stricter validation thresholds.
        skip_word_count: If True, bypasses the minimum 500-word density check.
    """
    logger.info(f"Tool: validate_multimodal_geometry called. Type of vision_proposal: {type(vision_proposal)}")
    logger.info(f"Content of vision_proposal: {vision_proposal}")
    
    # If the model passes a list, let's see if we can find the dictionary inside it,
    # or handle the list defensively if the model structure is slightly different.
    if isinstance(vision_proposal, list):
        if len(vision_proposal) > 0 and isinstance(vision_proposal[0], dict):
            # Model might have passed a list of labels
            labels = vision_proposal
            script = ""
        else:
            # Empty or unparseable
            labels = []
            script = ""
    elif isinstance(vision_proposal, dict):
        # Defensive De-nesting: Handle cases where the tool argument is nested under key names
        inner_prop = vision_proposal
        if 'vision_proposal' in vision_proposal and isinstance(vision_proposal['vision_proposal'], dict):
            inner_prop = vision_proposal['vision_proposal']
        elif 'vision_result' in vision_proposal and isinstance(vision_proposal['vision_result'], dict):
            inner_prop = vision_proposal['vision_result']
            
        script = inner_prop.get('script', '')
        labels = inner_prop.get('labels', [])
    else:
        script = ""
        labels = []
    
    # 1. Structural Audit
    word_count = len(script.split())
    if not skip_word_count and word_count < 500:
        return {
            "status": "REJECTED",
            "failure_type": "SCRIPT_DENSITY",
            "message": f"Script density too low ({word_count} words). Minimum 500 required.",
            "guidance": "Expand the script to include more navigational details and descriptive signposting (minimum 500 words)."
        }

    if len(labels) < 5:
        return {
            "status": "REJECTED",
            "failure_type": "INSUFFICIENT_ANCHORS",
            "message": f"Insufficient landmarks ({len(labels)}/5).",
            "guidance": "Identify more distinct semantic zones or architectural features on the map."
        }

    # 2. Geometric Audit (Euclidean distance on center points)
    collision_threshold = 300.0 if is_stress_test else 160.0
    
    # Calculate center points
    for label in labels:
        try:
            ymin, xmin, ymax, xmax = float(label['ymin']), float(label['xmin']), float(label['ymax']), float(label['xmax'])
            label['x'] = xmin + (xmax - xmin) / 2.0
            label['y'] = ymin + (ymax - ymin) / 2.0
        except (KeyError, ValueError):
            return {
                "status": "REJECTED",
                "failure_type": "TELEMETRY_INVALID",
                "message": "Missing or malformed numeric coordinates.",
                "guidance": "Provide valid 0-1000 bounding box coordinates for all landmarks."
            }

    for i, l1 in enumerate(labels):
        for j, l2 in enumerate(labels):
            if i >= j: continue
            dist = ((l1['x'] - l2['x'])**2 + (l1['y'] - l2['y'])**2)**0.5
            if dist < collision_threshold:
                return {
                    "status": "REJECTED",
                    "failure_type": "SPATIAL_COLLISION",
                    "message": f"Landmarks {l1['number']} and {l2['number']} are too close ({dist:.1f}px).",
                    "guidance": "Select landmarks that are more spatially distributed."
                }

    # 3. Canvas Edge-Clipping Check (Coordinate Boundary Gate)
    for label in labels:
        try:
            ymin, xmin, ymax, xmax = float(label['ymin']), float(label['xmin']), float(label['ymax']), float(label['xmax'])
            margin = 80.0
            if xmin < margin or ymin < margin or xmax > (1000.0 - margin) or ymax > (1000.0 - margin):
                clip_edge = "left" if xmin < margin else "top" if ymin < margin else "right" if xmax > (1000.0 - margin) else "bottom"
                return {
                    "status": "REJECTED",
                    "failure_type": "EDGE_CLIPPING",
                    "message": f"Landmark {label.get('number', '?')} ({label.get('location_name', 'Unnamed')}) is too close to the canvas edge (clipped on {clip_edge}).",
                    "guidance": f"Re-center and move the bounding box of '{label.get('location_name')}' slightly inward away from the {clip_edge} canvas border (minimum margin 80px)."
                }
        except (KeyError, ValueError):
            pass

    # 4. Route-Collision / Intersecting Path Check (Cartographic Path Gate)
    try:
        points = []
        sorted_labels = sorted(labels, key=lambda l: int(l.get('number', 1)))
        for label in sorted_labels:
            points.append((float(label['x']), float(label['y'])))
            
        segments = []
        for i in range(len(points) - 1):
            segments.append((points[i], points[i+1]))
            
        for i in range(len(segments)):
            for j in range(len(segments)):
                if abs(i - j) > 1:
                    p1, q1 = segments[i]
                    p2, q2 = segments[j]
                    if _do_intersect(p1, q1, p2, q2):
                        return {
                            "status": "REJECTED",
                            "failure_type": "ROUTE_INTERSECTION",
                            "message": f"Walking tour route contains self-intersecting segments! Stop {i+1}-{i+2} crosses Stop {j+1}-{j+2}.",
                            "guidance": "Reorder the landmark numbers or adjust their coordinates so that the walking path forms a clean, non-intersecting chronological loop."
                        }
    except Exception as e:
        logger.warning(f"Error calculating route intersection: {e}")

    return {
        "status": "PASSED",
        "message": "All production validation gates cleared.",
        "validated_telemetry": labels
    }

# Formal ADK Tool Wrapper
validate_multimodal_geometry = FunctionTool(func=validate_multimodal_geometry_func)
