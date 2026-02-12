"""
Conversation Summarization Service

Provides LLM-based summarization of conversation history
for efficient context management.
"""

from typing import List, Dict, Any
from app.agents import ChatbotAgent


async def summarize_conversation(
    message_pairs: List[Dict[str, str]],
    llm_agent: ChatbotAgent = None
) -> str:
    """
    Summarize a conversation using LLM.
    
    Args:
        message_pairs: List of message pairs with 'user' and 'assistant' keys
        llm_agent: Optional ChatbotAgent instance (creates new if None)
    
    Returns:
        Concise summary of the conversation
    """
    if not message_pairs:
        return ""
    
    # Build conversation text
    conversation_text = []
    for pair in message_pairs:
        conversation_text.append(f"Student: {pair['user']}")
        conversation_text.append(f"Advisor: {pair['assistant']}")
    
    conversation_str = "\n".join(conversation_text)
    
    # Create summarization prompt
    summary_prompt = f"""Summarize the following conversation between a student and academic advisor.

Focus on:
- Programme or courses discussed
- Key information provided
- Student's questions and goals
- Important decisions or recommendations made

Conversation:
{conversation_str}

Provide a brief, factual summary in 2-3 sentences. Focus on what's most relevant for future questions."""

    # Use LLM to generate summary
    if llm_agent is None:
        llm_agent = ChatbotAgent()
    
    from app.agents import Trace
    trace = Trace()
    
    response = await llm_agent.answer(
        summary_prompt,
        trace,
        context="",
        use_context=False
    )
    
    summary = response.get("answer", "").strip()
    
    return summary


def format_summary_for_context(summary: str, pair_count: int) -> str:
    """
    Format summary for inclusion in LLM context.
    
    Args:
        summary: The conversation summary
        pair_count: Number of message pairs that were summarized
    
    Returns:
        Formatted summary text
    """
    if not summary:
        return ""
    
    return f"""[Previous Conversation Summary - {pair_count} message pairs]
{summary}
[End of Summary]

"""
