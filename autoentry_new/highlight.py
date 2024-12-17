import fitz
import os
import stat
import api
def texts(ans):
    search_texts = []
    for i in ans['header']:
        search_texts.extend([ans['header'][i]])
    for line_item in ans['line_items']:
        for value in line_item:
            search_texts.extend([line_item[value]])
    for i in range(len(search_texts)):
        if (type(search_texts[i])) == float or int:
            search_texts[i]=str(search_texts[i])

    return search_texts





def highlight_text_with_debugging(input_pdf, output_pdf, search_texts, highlight_color=(1, 1, 0), highlight_limit=30):
    """
    Highlights the search text in the PDF based on the number of occurrences,
    limiting the text searched to the first `highlight_limit` characters of each search term.

    Parameters:
        input_pdf (str): Path to the input PDF file.
        output_pdf (str): Path to save the output PDF file.
        search_texts (list): List of search texts to highlight.
        highlight_color (tuple): RGB color for the highlight.
        highlight_limit (int): The maximum number of characters to search (e.g., 30).
    """

    try:
        doc = fitz.open(input_pdf)

        for page_num in range(len(doc)):
            page = doc[page_num]

            for search_text in search_texts:
                # Ensure the search text is properly encoded/decoded to avoid encoding issues
                chunk_to_highlight = str(search_text[:highlight_limit]).strip() if search_text else ''

                try:
                    # Search for the term in the current page, limited to `highlight_limit` characters
                    text_instances = page.search_for(chunk_to_highlight)

                    # Count the occurrences of the search text
                    occurrence_count = len(text_instances)

                    # Highlight each occurrence of the search text based on the count
                    for idx, rect in enumerate(text_instances):
                        if idx < occurrence_count:
                            adjusted_rect = fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2)
                            highlight = page.add_highlight_annot(adjusted_rect)
                            highlight.set_colors({"stroke": highlight_color})
                            highlight.update()

                except Exception as e:
                    api.logger.error(f"Error processing '{chunk_to_highlight}' on page {page_num + 1}: {e}")

        # Save the output PDF with the highlights
        doc.save(output_pdf)
        api.logger.info(f"\nSaved highlighted PDF as {output_pdf}.")

    except Exception as e:
        api.logger.error(f"Error processing file: {e}")
    
    finally:
        if 'doc' in locals():
            doc.close()

    return output_pdf
