
def create_feedback_blocks(title=None, question=None, response=None):
    blocks = []
    if title:
        blocks.extend([
            {"type": "section", "text": {"type": "mrkdwn", "text": title}},
            {"type": "divider"}
        ])
    if question:
        blocks.append({
            "type": "section", "text": {"type": "mrkdwn", "text": f":question: *Question* \n{question}"}
        })
    if response:
        blocks.append({
            "type": "section", "text": {"type": "mrkdwn", "text": f":page_with_curl: *Response* \n{response}"}
        })

    return blocks
