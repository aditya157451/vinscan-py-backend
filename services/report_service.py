from datetime import datetime
from typing import List, Dict, Literal, TypedDict, Optional, Any
from pydantic import BaseModel
import asyncio

from constants.prompts import phase_prompts
from utils.report_storage import save_report_to_database
from .open_router_service import OpenRouterService


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class ReportSection(BaseModel):
    title: str
    content: str


class Report(BaseModel):
    clientId: str
    summary: str
    sections: List[ReportSection]


async def generate_report(client_id: str, conversation_history: List[Message], client_info: dict = None) -> None:
    try:
        # Initialize report
        report = Report(
            clientId=client_id,
            summary="",
            sections=[]
        )

        # Add additional fields as a dictionary
        report_dict = report.model_dump()
        report_dict.update({
            "created_at": datetime.now(),
            "status": "generating"
        })

        # Save initial report status
        await save_report_to_database(report_dict)

        # Generate each section in parallel
        market_scan, competitor_scan, swot_analysis, recommendations = await asyncio.gather(
            generate_market_scan(
                conversation_history, client_info),
            generate_competitor_scan(
                conversation_history, client_info),
            generate_swot_analysis(
                conversation_history, client_info),
            generate_recommendations(
                conversation_history, client_info)
        )

        # Generate executive summary (after other sections are complete)
        summary = await generate_summary(conversation_history, [market_scan, competitor_scan, swot_analysis, recommendations], client_info)

        # Update report with all sections
        report_dict["summary"] = summary
        report_dict["sections"] = [
            {"title": "Market Scan", "content": market_scan},
            {"title": "Competitor Analysis", "content": competitor_scan},
            {"title": "SWOT Analysis", "content": swot_analysis},
            {"title": "Strategic Recommendations", "content": market_scan},
        ]
        report_dict["status"] = "completed"

        # Save completed report
        await save_report_to_database(report_dict)
    except Exception as error:
        print("Error generating report:", {error})

        failed_report: Report = {
            "client_id": client_id,
            "summary": "Report generation failed. Please contact support.",
            "sections": [],
            "created_at": datetime.now(),
            "status": "failed"
        }

        await save_report_to_database(failed_report)


async def generate_market_scan(
    conversation_history: List[Message],
    client_info: Optional[Dict[str, Any]] = None
) -> str:
    print("hellow")
    open_router = OpenRouterService.get_instance()

    market_scan_prompt = phase_prompts["market_scan"]

    # Create organization context
    organization_context = ""
    if client_info:
        organization_context = f"""
            This report is for {client_info.get('name')}, {client_info.get('position')} at {
            client_info.get('website_url') or "their organization"
        }.
        """

    prompt = f"""
    {organization_context}
    Based on the following interview conversation, generate a comprehensive Market Scan section for a business report.
    
    {market_scan_prompt}
    
    Format the response as a well-structured report section with headings, bullet points, and paragraphs.
    Only include information that can be reasonably inferred from the conversation and website data.
    If certain information is missing, acknowledge the gaps rather than making up details.
    
    Conversation history:
    {chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}
    """

    return await open_router.chat([{"role": "system", "content": prompt}])


async def generate_competitor_scan(
    conversation_history: List[Message],
    client_info: Optional[Dict[str, Any]] = None
) -> str:
    open_router = OpenRouterService.get_instance()

    competitor_scan_prompt = phase_prompts["competitor_scan"]

    organization_context = ""
    if client_info:
        organization_context = f"""
            This report is for {client_info.get('name')}, {client_info.get('position')} at {
            client_info.get('website_url') or "their organization"
        }.
        """

    prompt = f"""
    {organization_context}
    Based on the following interview conversation, generate a comprehensive Competitor Scan section for a business report.
    
    {competitor_scan_prompt}
    
    Format the response as a well-structured report section with headings, bullet points, and paragraphs.
    Only include information that can be reasonably inferred from the conversation and website data.
    If certain information is missing, acknowledge the gaps rather than making up details.
    
    Conversation history:
    {chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}
    """

    return await open_router.chat([{"role": "system", "content": prompt}])


async def generate_swot_analysis(
    conversation_history: List[Message],
    client_info: Optional[Dict[str, Any]] = None
) -> str:
    open_router = OpenRouterService.get_instance()

    organization_context = ""
    if client_info:
        organization_context = f"""
            This report is for {client_info.get('name')}, {client_info.get('position')} at {
            client_info.get('website_url') or "their organization"
        }.
        """

    prompt = f"""
    {organization_context}
    Based on the following interview conversation, generate a SWOT Analysis section for a business report.
    
    The SWOT Analysis should include:
    1. Strengths: Internal factors that give the organization an advantage over others
    2. Weaknesses: Internal factors that place the organization at a disadvantage
    3. Opportunities: External factors that the organization could capitalize on
    4. Threats: External factors that could cause trouble for the organization
    
    For each category, provide 3-5 bullet points with brief explanations.
    Format the response as a well-structured report section with clear headings for each SWOT component.
    Only include information that can be reasonably inferred from the conversation and website data.
    If certain information is missing, acknowledge the gaps rather than making up details.
    
    Conversation history:
    {chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}
    """

    return await open_router.chat([{"role": "system", "content": prompt}])


async def generate_recommendations(
    conversation_history: List[Message],
    client_info: Optional[Dict[str, Any]] = None
) -> str:
    open_router = OpenRouterService.get_instance()

    organization_context = ""
    if client_info:
        organization_context = f"""
            This report is for {client_info.get('name')}, {client_info.get('position')} at {
            client_info.get('website_url') or "their organization"
        }.
        """

    prompt = f"""
    {organization_context}
    Based on the following interview conversation, generate a Strategic Recommendations section for a business report.
    
    Provide 5-7 actionable recommendations that:
    1. Address key challenges identified in the conversation
    2. Leverage the organization's strengths
    3. Take advantage of market opportunities
    4. Mitigate potential threats
    5. Are specific, measurable, achievable, relevant, and time-bound (SMART)
    
    For each recommendation, include:
    - A clear action statement
    - Brief rationale
    - Potential implementation steps
    
    Format the response as a well-structured report section with numbered recommendations.
    Only include recommendations that can be reasonably inferred from the conversation and website data.
    If certain information is missing, acknowledge the limitations rather than making up details.
    
    Conversation history:
    {chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}
    """

    return await open_router.chat([{"role": "system", "content": prompt}])


async def generate_summary(
    conversation_history: List[Message],
    sections: List[str],
    client_info: Optional[Dict[str, Any]] = None
) -> str:
    open_router = OpenRouterService.get_instance()

    organization_context = ""
    if client_info:
        organization_context = f"""
            This report is for {client_info.get('name')}, {client_info.get('position')} at {
            client_info.get('website_url') or "their organization"
        }.
        """

    prompt = f"""
    {organization_context}
    Based on the following interview conversation and report sections, generate an Executive Summary for a business report.
    
    The summary should:
    1. Be approximately 250-300 words
    2. Highlight key findings from each section
    3. Provide a high-level overview of the business situation
    4. Mention 2-3 critical recommendations
    
    Format the response as a concise, professional executive summary without headings.
    Only include information that appears in the conversation, report sections, or website data.
    
    Conversation history:
    {chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}
    
    Report Section:
    {chr(10).join(sections)}
    """

    return await open_router.chat([{"role": "system", "content": prompt}])
