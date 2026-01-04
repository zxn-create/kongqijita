import numpy as np
import os
import scipy.io.wavfile as wavfile

def validate_guitar_sounds():
    """Validate generated guitar sounds quality"""
    print("Validating sound quality...")
    
    base_path = "guitar_samples/"
    issues = []
    
    # Check all expected files
    expected_files = {
        'single_notes': ['E4.wav', 'B.wav', 'G.wav', 'D.wav', 'A.wav', 'E2.wav'],
        'chords': ['C_major.wav', 'G_major.wav', 'D_major.wav', 
                  'A_minor.wav', 'E_minor.wav', 'F_major.wav'],
        'effects': ['pick_noise.wav', 'string_slide.wav', 'harmonic.wav']
    }
    
    for category, files in expected_files.items():
        for file in files:
            filepath = os.path.join(base_path, category, file)
            if not os.path.exists(filepath):
                issues.append(f"Missing: {filepath}")
            else:
                # Analyze audio quality
                try:
                    sample_rate, data = wavfile.read(filepath)
                    duration = len(data) / sample_rate
                    rms = np.sqrt(np.mean(data.astype(float)**2)) / 32767.0
                    
                    print(f"OK {category}/{file}: {duration:.2f}s, RMS: {rms:.4f}")
                    
                    # Quality checks
                    if duration < 0.5:
                        issues.append(f"Short duration: {file} ({duration:.2f}s)")
                    if rms < 0.01:
                        issues.append(f"Low volume: {file} (RMS: {rms:.4f})")
                        
                except Exception as e:
                    issues.append(f"Read failed: {file} - {e}")
    
    # Output results
    print("\n" + "="*50)
    if issues:
        print("Issues found:")
        for issue in issues:
            print(issue)
    else:
        print("All sound files validated successfully!")

if __name__ == "__main__":
    validate_guitar_sounds()
