working_labels = {"sitting", "using_laptop", "writing", "reading", "start_pomodoro", "stop_pomodoro"}

def determine_final_status(history):
    if not history: return "Working"
    
    # Simple majority voting atau thresholding
    distracted_count = sum(1 for status in history if status['label'] not in working_labels)
    threshold = len(history) - 1

    if distracted_count >= threshold:
        return "Distracted"
    return "Working"