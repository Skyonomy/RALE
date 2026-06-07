import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class AuditorAgent:
    """
    The Auditor Agent: Deterministic Semantic-to-Geometric Grounding Layer.
    Calculates absolute safe-zone centers from semantic bounding boxes
    and applies rigorous mathematical validation (Track 2: Optimize).
    """

    def audit_output(self, vision_result: Dict, is_stress_test: bool = False) -> Tuple[bool, str]:
        """
        Validates bounding boxes and calculates final [x,y] anchor points.
        Returns (is_valid, error_message). Injects 'x' and 'y' into labels.
        """
        logger.info("Auditor: [PRODUCTION GATE] Initiating deterministic validation scan...")
        
        script = vision_result.get('script', '')
        labels = vision_result.get('labels', [])

        # 1. Fast Structural Checks
        word_count = len(script.split())
        if word_count < 380:
            msg = f"REJECTED: Script density below threshold ({word_count} words)"
            logger.warning(f"Auditor: {msg}")
            return False, msg

        if len(labels) < 5:
            msg = f"REJECTED: Insufficient tour stops ({len(labels)}/5)"
            logger.warning(f"Auditor: {msg}")
            return False, msg

        # 2. Pass 1: Bounding Box Extraction & Center Calculation
        for label in labels:
            try:
                ymin = float(label['ymin'])
                xmin = float(label['xmin'])
                ymax = float(label['ymax'])
                xmax = float(label['xmax'])
            except (KeyError, ValueError):
                return False, f"REJECTED: Marker {label.get('number', '?')} missing telemetry"

            if not (0 <= ymin <= 1000 and 0 <= xmin <= 1000 and 0 <= ymax <= 1000 and 0 <= xmax <= 1000):
                return False, f"REJECTED: Marker {label.get('number', '?')} coordinates OOB"

            if xmin >= xmax or ymin >= ymax:
                return False, f"REJECTED: Marker {label.get('number', '?')} invalid geometry"

            # Calculate deterministic anchor (center)
            calc_x = xmin + ((xmax - xmin) / 2.0)
            calc_y = ymin + ((ymax - ymin) / 2.0)
            
            # Inject calculated anchor for downstream tools (UI, Compositor, Audio)
            label['x'] = calc_x
            label['y'] = calc_y
            # Also preserve 'name' for legacy downstream compatibility
            if 'location_name' in label and 'name' not in label:
                label['name'] = label['location_name']

        # 3. Spatial Collision Audit (Euclidean Distance) - PRIORITIZED IN STRESS TEST
        collision_threshold = 300.0 if is_stress_test else 80.0
        
        for i, l1 in enumerate(labels):
            for j, l2 in enumerate(labels):
                if i >= j: continue
                
                dist = ((l1['x'] - l2['x'])**2 + (l1['y'] - l2['y'])**2)**0.5
                if dist < collision_threshold:
                    msg = f"REJECTED: Spatial collision (Dist: {dist:.1f}px)"
                    logger.warning(f"Auditor: {msg}")
                    return False, msg

        # 4. Pass 2: Bounding Box Size Validation (After collision check)
        for label in labels:
            ymin = float(label['ymin'])
            xmin = float(label['xmin'])
            ymax = float(label['ymax'])
            xmax = float(label['xmax'])
            bbox_type = label.get('bbox_type', 'room')
            # Area is calculated on 1000x1000 scale. Total area is 1,000,000.
            area_percentage = ((xmax - xmin) * (ymax - ymin)) / 10000.0

            if area_percentage < 0.1:
                return False, f"REJECTED: Marker {label.get('number', '?')} area too small"

            if bbox_type == 'landmark' and area_percentage > 8.0:
                return False, f"REJECTED: Marker {label.get('number', '?')} landmark too large"
            elif bbox_type == 'room' and area_percentage > 12.0:
                return False, f"REJECTED: Marker {label.get('number', '?')} room too large"
            elif bbox_type == 'broad_area' and area_percentage > 25.0:
                return False, f"REJECTED: Marker {label.get('number', '?')} broad area too large"

        logger.info("Auditor: PASSED: Production validation successful")
        return True, ""
