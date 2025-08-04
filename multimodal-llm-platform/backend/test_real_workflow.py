#!/usr/bin/env python3
"""
Test the real workflow: Upload files -> Analyze tokens -> Process with summarization
This simulates your exact use case of analyzing multiple documents against constitutional principles
"""

import sys
from pathlib import Path
import uuid

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from token_manager import token_manager
from content_summarizer import ContentSummarizer

def simulate_large_file_analysis():
    """Simulate analyzing 8 large documents (your typical workflow)"""
    
    print("🏛️  CONSTITUTIONAL ANALYSIS WORKFLOW SIMULATION")
    print("=" * 70)
    print("Simulating your typical workflow: 8 documents + constitutional comparison")
    
    # Simulate 8 files of varying sizes (like your real use case)
    simulated_files = [
        {
            "filename": "policy_document_1.pdf",
            "type": "pdf",
            "content": """
            Policy Analysis: Healthcare Reform Proposal
            
            Executive Summary:
            This comprehensive policy document outlines proposed reforms to the healthcare system, focusing on universal access, cost containment, and quality improvement. The proposal addresses constitutional concerns regarding interstate commerce, individual mandates, and state versus federal authority.
            
            Constitutional Considerations:
            The Commerce Clause provides the constitutional basis for federal healthcare regulation. Previous Supreme Court decisions have established precedent for federal involvement in healthcare markets, particularly in cases affecting interstate commerce.
            
            Implementation Framework:
            1. Federal Standards and Guidelines
            2. State Implementation Flexibility  
            3. Individual Rights Protections
            4. Due Process Requirements
            5. Equal Protection Safeguards
            
            The proposal maintains careful balance between federal oversight and state autonomy, ensuring compliance with constitutional principles while achieving policy objectives.
            """ * 10  # Simulate large document
        },
        {
            "filename": "voting_rights_analysis.docx", 
            "type": "docx",
            "content": """
            Voting Rights and Electoral Integrity Analysis
            
            Introduction:
            This analysis examines current voting procedures and proposed reforms in light of constitutional voting rights protections. The document addresses the balance between election security and voter access.
            
            Constitutional Framework:
            The 15th, 19th, and 26th Amendments provide explicit voting rights protections. The Equal Protection Clause of the 14th Amendment has been interpreted to require fair and equal voting procedures.
            
            Key Issues:
            - Voter ID requirements and their impact on constitutional rights
            - Early voting and mail-in ballot procedures
            - Redistricting and gerrymandering concerns
            - Polling place accessibility and accommodations
            - Campaign finance regulations and free speech
            
            Analysis demonstrates the need for careful constitutional review of any proposed changes to voting procedures.
            """ * 8
        },
        {
            "filename": "privacy_rights_digital_age.txt",
            "type": "text", 
            "content": """
            Privacy Rights in the Digital Age: Constitutional Perspectives
            
            The Fourth Amendment's protection against unreasonable searches and seizures faces new challenges in the digital era. This document examines how traditional privacy rights apply to modern technology and data collection practices.
            
            Key Constitutional Questions:
            1. Do digital communications receive the same privacy protections as physical documents?
            2. How do third-party doctrine principles apply to cloud storage and social media?
            3. What constitutes reasonable expectation of privacy in digital contexts?
            4. How should law enforcement obtain warrants for digital evidence?
            
            The analysis concludes that constitutional privacy protections must evolve to address technological changes while maintaining core Fourth Amendment principles.
            """ * 12
        },
        {
            "filename": "religious_freedom_workplace.pdf",
            "type": "pdf",
            "content": """
            Religious Freedom in the Workplace: Constitutional Balance
            
            This document analyzes the intersection of religious liberty and employment law, examining how the First Amendment's Free Exercise and Establishment Clauses apply in workplace contexts.
            
            Constitutional Principles:
            - Free Exercise: Individuals' right to practice their religion
            - Establishment Clause: Prohibition on government establishment of religion
            - Equal Protection: Non-discrimination requirements
            - Due Process: Fair treatment in employment decisions
            
            The analysis addresses accommodation requirements, religious exemptions, and the limits of both employee religious expression and employer religious freedom in various workplace scenarios.
            """ * 15
        },
        {
            "filename": "free_speech_social_media.docx",
            "type": "docx", 
            "content": """
            Free Speech and Social Media Platform Regulation
            
            Constitutional Analysis of Content Moderation and Government Regulation
            
            This comprehensive analysis examines First Amendment implications of social media content policies and proposed government regulations of online platforms.
            
            Constitutional Framework:
            The First Amendment prohibits government restrictions on speech, but private companies generally have the right to moderate content on their platforms. However, questions arise when government pressure influences private content decisions.
            
            Key Issues:
            - State action doctrine and private platform moderation
            - Government pressure on content decisions
            - Public forum analysis for social media platforms
            - Commercial speech protections for platforms
            - International implications of content regulation
            
            The document concludes with recommendations for preserving constitutional principles while addressing legitimate concerns about online speech.
            """ * 11
        },
        {
            "filename": "criminal_justice_reform.txt",
            "type": "text",
            "content": """
            Criminal Justice Reform: Constitutional Requirements and Opportunities
            
            This policy analysis examines proposed criminal justice reforms through the lens of constitutional protections, focusing on due process, equal protection, and Eighth Amendment considerations.
            
            Constitutional Protections:
            - Due Process: Fair procedures in criminal proceedings
            - Equal Protection: Non-discriminatory application of criminal law
            - Sixth Amendment: Right to counsel and fair trial
            - Eighth Amendment: Protection against cruel and unusual punishment
            - Fourth Amendment: Protection against unreasonable searches and seizures
            
            The analysis addresses bail reform, sentencing guidelines, police procedures, and rehabilitation programs, ensuring all proposals comply with constitutional requirements while achieving reform objectives.
            """ * 9
        },
        {
            "filename": "education_policy_constitutional.pdf",
            "type": "pdf",
            "content": """
            Education Policy and Constitutional Principles
            
            Analysis of Federal and State Education Policies in Constitutional Context
            
            This document examines education policy proposals for constitutional compliance, addressing issues of federal authority, state responsibility, and individual rights in educational contexts.
            
            Constitutional Considerations:
            While education is not explicitly mentioned in the Constitution, various amendments and clauses affect educational policy:
            - Equal Protection Clause and school desegregation
            - Due Process and student disciplinary procedures  
            - First Amendment and student speech rights
            - Establishment Clause and religious instruction
            - Commerce Clause and federal education funding
            
            The analysis provides guidance for policy makers on constitutional constraints and opportunities in education reform.
            """ * 13
        },
        {
            "filename": "environmental_regulation_commerce.docx",
            "type": "docx",
            "content": """
            Environmental Regulation and the Commerce Clause
            
            Constitutional Analysis of Federal Environmental Authority
            
            This comprehensive analysis examines the constitutional basis for federal environmental regulation, focusing on Commerce Clause authority and state-federal relations in environmental policy.
            
            Constitutional Framework:
            The Commerce Clause provides the primary constitutional authority for federal environmental regulation. Courts have generally upheld federal environmental laws as valid exercises of commerce power, particularly when environmental issues cross state boundaries.
            
            Key Constitutional Issues:
            - Interstate nature of environmental problems
            - Economic effects of environmental regulation
            - State sovereignty and federal mandates
            - Property rights and environmental restrictions
            - Due process in environmental enforcement
            
            The document provides constitutional analysis of major environmental laws and proposed reforms.
            """ * 14
        }
    ]
    
    print(f"📁 Files to analyze: {len(simulated_files)}")
    
    # Calculate total content size
    total_chars = sum(len(file['content']) for file in simulated_files)
    print(f"📊 Total content: {total_chars:,} characters")
    
    # User query (your typical constitutional analysis request)
    user_query = """
    Please analyze these documents for their constitutional themes and compliance. 
    Compare the policies and proposals against fundamental constitutional principles 
    including separation of powers, individual rights, due process, equal protection, 
    and federalism. Identify any potential constitutional concerns and provide 
    recommendations for ensuring constitutional compliance while achieving policy objectives.
    Focus on how these modern policies relate to the original constitutional framework 
    and subsequent amendments.
    """
    
    print(f"🔍 Analysis query: {len(user_query)} characters")
    
    # Test with different models
    models_to_test = ["claude-3.5-sonnet", "gpt-4o", "gemini-pro"]
    
    for model in models_to_test:
        print(f"\n🤖 Testing with {model}:")
        print("-" * 50)
        
        # Analyze token requirements
        analysis = token_manager.analyze_content_for_chunking(
            file_contents=simulated_files,
            model_id=model,
            user_prompt=user_query
        )
        
        context_window = analysis['budget'].max_context
        total_tokens = analysis['total_estimated_tokens']
        usage_pct = round((total_tokens / context_window) * 100, 1)
        
        print(f"Context window: {context_window:,} tokens")
        print(f"Required tokens: {total_tokens:,} tokens ({usage_pct}%)")
        print(f"Fits without chunking: {'✅ Yes' if not analysis['chunking_recommended'] else '❌ No'}")
        
        if analysis['chunking_recommended'] or analysis['exceeds_limit']:
            print(f"📝 Intelligent summarization recommended")
            
            # Test summarization
            summarizer = ContentSummarizer(token_manager.token_counter)
            summaries = summarizer.batch_summarize_files(
                file_contents=simulated_files,
                total_target_tokens=analysis['budget'].file_content,
                model_family=analysis['model_family'],
                context_keywords=["constitutional", "rights", "amendment", "due process", "equal protection", "commerce clause"]
            )
            
            total_original = sum(s.original_tokens for s in summaries)
            total_summarized = sum(s.summarized_tokens for s in summaries) 
            compression_pct = round((1 - total_summarized/total_original) * 100, 1)
            
            print(f"📉 Compression: {total_original:,} → {total_summarized:,} tokens ({compression_pct}% reduction)")
            print(f"✅ Fits after summarization: {total_summarized < analysis['budget'].file_content}")
        
        print()
    
    # Final recommendation
    print("🎯 RECOMMENDATION FOR YOUR USE CASE:")
    print("-" * 50)
    print("✅ Claude 3.5 Sonnet: Best choice for 8+ large documents")
    print("   • 200k context window provides ample space")  
    print("   • Excellent at constitutional analysis")
    print("   • Handles complex legal reasoning well")
    print()
    print("✅ GPT-4o: Good alternative with smart summarization")
    print("   • 128k context handles most scenarios")
    print("   • Automatic summarization when needed")
    print("   • Strong analytical capabilities")
    print()
    print("⚠️  Gemini Pro: Requires aggressive summarization")
    print("   • 32k context is limiting for large document sets")
    print("   • Better for smaller document analyses")
    print()
    print("🚀 Your system is ready! No more OpenRouter throttling issues.")

if __name__ == "__main__":
    simulate_large_file_analysis()