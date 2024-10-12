
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

def create_image(a4_size):
    """Create a new A4-sized image with a white background."""
    return Image.new('RGB', a4_size, color='white')

def load_font(font_path, font_size):
    """Load the specified font with the given size."""
    try:
        return ImageFont.truetype(font_path, font_size)
    except IOError:
        st.error("Font file not found. Please check the path.")
        return None

def text_fits_on_page(draw, text, font, max_width, max_height):
    """Check if the text fits within the specified dimensions."""
    current_height = 0
    for line in text.split('\n'):
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width > max_width or current_height + height > max_height:
            return False
        current_height += height + 8  # Line spacing
    return True

def split_text_into_lines(draw, text, max_width, font):
    """Split text into lines that fit within the maximum width."""
    lines = []
    current_line = []

    for line in text.split('\n'):
        if line.strip() == "":  # Preserve empty lines
            lines.append("")  # Preserve formatting for empty lines
            continue

        if line.startswith("## "):  # Heading
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
            lines.append(line[3:])  # Add heading without "## "
            continue

        for word in line.split():
            current_line.append(word)
            line_text = " ".join(current_line)
            if draw.textbbox((0, 0), line_text, font=font)[2] - draw.textbbox((0, 0), line_text, font=font)[0] > max_width:
                current_line.pop()  # Remove the last word
                lines.append(" ".join(current_line))  # Append the valid line
                current_line = [word]  # Start a new line

        if current_line:
            lines.append(" ".join(current_line))

    return "\n".join(lines)

def adjust_font_size(draw, text, font_path, max_width, max_height):
    """Dynamically adjust the font size to fit the text on the page."""
    font_size = 60  # Starting font size
    while font_size > 10:
        font = load_font(font_path, font_size)
        formatted_text = split_text_into_lines(draw, text, max_width - 200, font)
        if text_fits_on_page(draw, formatted_text, font, max_width - 200, max_height - 200):
            return formatted_text, font
        font_size -= 1  # Decrease font size
    return "", None  # Return empty if no suitable font size found

def draw_text(draw, formatted_text, x, y, heading_font, font, font_color, previous_lines=set()):
    """Draw the text onto the image and remove duplicate lines."""
    lines = formatted_text.split('\n')
    last_was_heading = False  # Track if the last line was a heading
    drawn_lines = previous_lines  # Store lines that have already been drawn
    previous_line = ""  # Initialize previous_line as an empty string

    for line in lines:
        if line.strip() == "":  # If line is empty, skip to next
            y += font.size + 8  # Maintain spacing for empty lines
            continue

        if line in drawn_lines:  # Skip the line if it's a duplicate
            continue

        if line.startswith("## "):  # Heading
            draw.text((x, y), line[3:], font=heading_font, fill=font_color)
            y += heading_font.size + 12  # Increased spacing for headings
            last_was_heading = True
            drawn_lines.add(line)  # Mark heading as drawn
            previous_line = line  # Update previous_line to the current heading
            continue  # Move to the next line after heading

        # Check if the current line is the same as the last line drawn
        if previous_line.strip() == line.strip():
            continue  # Skip drawing if it's the same as the last line

        if line.startswith("**") and line.endswith("**"):  # Bold text
            draw.text((x, y), line[2:-2], font=font, fill=font_color)
            y += font.size + 8  # Standard spacing for bold text
            last_was_heading = False
        else:  # Normal text
            draw.text((x, y), line, font=font, fill=font_color)
            y += font.size + 8  # Standard spacing for normal text
        
        drawn_lines.add(line)  # Add the drawn line to the set of drawn lines
        previous_line = line  # Update previous_line to the current line
            
    return y, drawn_lines  # Return final y position and drawn lines

def text_to_handwriting(text, font_path, output_path, font_color, previous_texts=set()):
    """Convert text to handwriting and save as an image."""
    a4_size = (2000, 3000)  # A4 size at 300 DPI
    img = create_image(a4_size)
    draw = ImageDraw.Draw(img)

    heading_font = load_font(font_path, 120)  # Heading font
    font = load_font(font_path, 100)  # Standard font

    if not heading_font or not font:
        return None

    formatted_text, font = adjust_font_size(draw, text, font_path, a4_size[0], a4_size[1])
    
    if not formatted_text or not font:
        st.error("Could not format the text to fit the page.")
        return None

    _, drawn_lines = draw_text(draw, formatted_text, 100, 100, heading_font, font, font_color, previous_texts)
    img.save(output_path)
    return output_path, drawn_lines

# Streamlit user interface
st.set_page_config(page_title="Text to Handwriting Converter", layout="wide")
st.title("🖋️ Text to Handwriting Converter")
st.markdown("### Convert your text into beautiful handwriting with ease!")

# Sidebar for font and color selection
st.sidebar.header("Customization Options")
text_input_method = st.sidebar.radio("Choose input method:", ("Text Input", "Upload Text File"))

# Get user text input
user_text = ""
if text_input_method == "Text Input":
    user_text = st.sidebar.text_area("Enter the text you want to convert to handwriting:", height=200)
elif text_input_method == "Upload Text File":
    uploaded_file = st.sidebar.file_uploader("Upload a text file (.txt)", type='txt')
    if uploaded_file is not None:
        user_text = uploaded_file.read().decode('utf-8')
        st.sidebar.text_area("Text from file:", user_text, height=200)

# Limit user input to a maximum of 1000 words
if user_text and len(user_text.split()) > 1000:
    st.error("Please enter no more than 1000 words.")
else:
    available_fonts = {
        "Cedarville Cursive": "fonts/CedarvilleCursive-Regular.ttf",
        "Patrick Hand": "fonts/PatrickHand-Regular.ttf",
        "Permanent Marker": "fonts/PermanentMarker-Regular.ttf",
        "Dancing Script": "fonts/DancingScript-VariableFont_wght.ttf",
        "Quicksand": "fonts/Quicksand-VariableFont_wght.ttf",
        "Sacramento": "fonts/Sacramento-Regular.ttf",
        "Satisfy": "fonts/Satisfy-Regular.ttf",
        "The Girl Next Door": "fonts/TheGirlNextDoor-Regular.ttf",
    }

    font_selection = st.sidebar.selectbox("Select Handwriting Font:", list(available_fonts.keys()))
    font_color = st.sidebar.color_picker("Pick a font color:", "#000000")  # Default to black

    previous_texts = set()  # Initialize a set to store previously drawn texts

    if st.sidebar.button("Convert to Handwriting", key="convert_button"):
        if user_text:
            selected_font_path = available_fonts[font_selection]
            output_image_path, drawn_lines = text_to_handwriting(user_text, selected_font_path, 'handwriting_output.jpg', font_color, previous_texts)
            previous_texts.update(drawn_lines)  # Update the set with newly drawn lines

            if output_image_path:
                st.success("Handwriting conversion complete!")
                img = Image.open(output_image_path)
                st.image(img, caption='Handwritten Output', use_column_width=True)

                with open(output_image_path, "rb") as f:
                    st.download_button("Download Handwritten Image", f, file_name='handwriting_output.jpg', mime="image/jpeg")
        else:
            st.error("Please enter text or upload a text file.")

# Add footer with information
st.markdown("---")
st.markdown("© 2024 Text to Handwriting Converter | Made by Shivam Rawat")
