#!/usr/bin/env python3
"""
Create a demo MIDI file for the MobilSheets bass clarinet video demo
"""

from music21 import stream, note, meter, tempo, duration, key, scale

def create_demo_midi():
    """Create a simple bass clarinet demo MIDI file"""
    
    # Create a new score
    score = stream.Score()
    
    # Set up the basic musical elements
    score.append(tempo.MetronomeMark(number=120))  # 120 BPM
    score.append(key.KeySignature(2))  # D Major (good for bass clarinet)
    score.append(meter.TimeSignature('4/4'))
    
    # Create a simple melody suitable for bass clarinet
    # These are in the comfortable range for bass clarinet
    notes_sequence = [
        ('D3', 1.0),   # D below middle C
        ('E3', 1.0),   # E
        ('F#3', 1.0),  # F#
        ('G3', 1.0),   # G
        ('A3', 2.0),   # A (longer note)
        ('G3', 1.0),   # G
        ('F#3', 1.0),  # F#
        ('E3', 2.0),   # E (longer note)
        ('D3', 4.0),   # D (whole note)
    ]
    
    # Create the melody part
    melody = stream.Part()
    melody.append(meter.TimeSignature('4/4'))
    
    for note_name, note_duration in notes_sequence:
        n = note.Note(note_name)
        n.duration = duration.Duration(note_duration)
        melody.append(n)
    
    # Add the melody to the score
    score.append(melody)
    
    return score

if __name__ == "__main__":
    # Create the demo MIDI
    demo_score = create_demo_midi()
    
    # Save to the output directory
    import os
    os.makedirs("backend/output", exist_ok=True)
    
    output_path = "backend/output/demo_bass_clarinet.mid"
    demo_score.write('midi', fp=output_path)
    
    print(f"✅ Demo MIDI file created: {output_path}")
    print("🎷 Perfect for your bass clarinet video demo!")
