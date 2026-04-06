# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview

**What is DocuBot trying to do?**  
Describe the overall goal in 2 to 3 sentences.

> DocuBot is a lightweight retrieval-based question answering system that helps users find relevant information from a collection of documents. It uses substring-based keyword matching and a simple scoring function to identify and rank relevant document snippets for a given query. When paired with an LLM, it can generate answers grounded in the retrieved evidence.

**What inputs does DocuBot take?**  
For example: user question, docs in folder, environment variables.

> DocuBot takes a user query and a collection of documents from a local folder as inputs. On RAG mode it takes an LLM client and environment variables for generating answers.

**What outputs does DocuBot produce?**

> DocuBot outputs the most elevant document snippets and their filenames. In retrieval-only mode, these snippets are returned as formatted text. In RAG mode, it generates an answer based on the retrieved evidence.

---

## 2. Retrieval Design

**How does your retrieval system work?**  
Describe your choices for indexing and scoring.

- How do you turn documents into an index?
- How do you score relevance for a query?
- How do you choose top snippets?

> DocuBot uses a simple retrieval pipeline that combines an inverted index, substring-based scoring, and paragraph-level snippet selection.

> To build the index each document is lowercased, split into words, and cleaned by removing punctuation. Then, each unique word is mapped to the filenames it appears in, creating an inverted index of word --> documents. I used a set per document to avoid duplicate entires and keep the index clear. 

> For scoring, I lowercase and clean the query, remove stop words, and then check whether each query word appears as a substring in the document text. The score is based on how many query words match, so documents with more matching terms are considered to be more relevant. 

> First, I use the index to get candidate documents and then score and sort them in descending order. From the top documents, I extract the most relevant paragraphss by splitting the text and scoring each paragraph based on query matches. In the end I return the highest scoring paragraphs, and filter out any documents that don't have meaningful matches.

**What tradeoffs did you make?**  
For example: speed vs precision, simplicity vs accuracy.

> In this system I prioritized simplicity and speed over precision and accuracy.  

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**  
Briefly describe how each mode behaves.

- Naive LLM mode: 
- Retrieval only mode:
- RAG mode:

> In Naive LLM mode, the LLM is called direclty with the full set of documents without any retrieval step. Resulting in the model trying to answer using all available information at once.

> In Retrieval-only mode, the LLM is not used at all. The system relies entirely on the inverted index and scoring logic to find and return the most relevant document snippets. It mainly displays the retrieved text without generating a new answer.

> In RAG mode the system uses retrieval to select the most relevant snippets, and then passes those snippets to the LLM. The LLM then generates an answer grounded in the retrieved context.

**What instructions do you give the LLM to keep it grounded?**  
Summarize the rules from your prompt. For example: only use snippets, say "I do not know" when needed, cite files.

> To keep the LLM grounded, it can only answer using retrieved snippets and must say "I do not know based on these docs" if the snippets do not contain enough information. 

---

## 4. Experiments and Comparisons

Run the **same set of queries** in all three modes. Fill in the table with short notes.

You can reuse or adapt the queries from `dataset.py`.

| Query | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes |
|------|---------------------------------|--------------------------------------|---------------------------|-------|
| Example: Where is the auth token generated? | Harmful | Helpful | Helpful | Naive hallucinates and can be vague. Retrieval shows the exact file. RAG explains clearly using context. |
| Example: How do I connect to the database? | Harmful | Somewhat Helpful | Somewhat Helpful | RAG avoided hallucination by refusing to answer, but was overly conservative since some relevant info was available. |
| Example: Which endpoint lists all users? | Harmful | Harmful | Helpful | RAG refused to answer due to weak evidence, avoiding hallucination but missing partial useful info. |
| Example: How does a client refresh an access token? | Harmful | Helpful | Helpful | Retrieval returns the exact instruction. RAG creates a more clear answer. |

**What patterns did you notice?**  

- When does naive LLM look impressive but untrustworthy?  
- When is retrieval only clearly better?  
- When is RAG clearly better than both?

> The Naive LLM often looks impressive when it gives detailed, confident answers that follow common patterns. However, it is untrustworthy when the question requires specific information from the provided documents because it relies on general knowledge which causes it to generate plausible but incorrect answers.

> Retrieval only is clearly better when the answer exists explicitly in the documents and needs to be returned as written. It avoids hallucination and reliably surfaces the correct source text, especially for specific questions like endpoints, configuration details or exact instructions.

> RAG is clearly better than both when the answer requires both accurate retrieval and a clear, readable explanation.

---

## 5. Failure Cases and Guardrails

**Describe at least two concrete failure cases you observed.**  
For each one, say:

- What was the question?  
- What did the system do?  
- What should have happened instead?

> [Failure case 1] Question: Which endpoint lists all users? On retrieval mode, the system returns relevant but indirect information which did not directly answer the question.  What should have happened: the system should have either retrieved a document that explicitly lists the users endpoint or refused to answer if no relevant evidence was found, instead of returning a vague or unrelated snippet.

> [Failure case 2] Question: Is there any mention of payment processing in these docs? On retrieval mode the system returned content from DATABASE.md that was unrelated to payment processing. What should hve happened: they system should have recognized there was no relevant information about payment processing and returned no results, instead of returning unrelated content.

**When should DocuBot say “I do not know based on the docs I have”?**  
Give at least two specific situations.

> DocuBot should say "I do not know based on the docs I have" if the user asks about a topic like payment processing and none of the documents mention it. 

> It should also respond this way when the if the retrieved info is too weak or indirect such as when the input asked "How do I connect to the database?"

**What guardrails did you implement?**  
Examples: refusal rules, thresholds, limits on snippets, safe defaults.

> I added a filter during retrieval by skipping documents with a score less than 1, ensuring that only documents with at least one keyword match are considered. I also restricted each document to only its most relevant paragraphs, which helped reduce noise and avoid returning large irrelevant chunks of text.

---

## 6. Limitations and Future Improvements

**Current limitations**  
List at least three limitations of your DocuBot system.

1. Substring-based matching can return irrelevant results.
2. Lack of semantic understanding.
3. RAG can be overly conservative.

**Future improvements**  
List two or three changes that would most improve reliability or usefulness.

1. Use semantic serch.
2. Improve scoring such as weighting important terms.
3. Adjusting the guardrail to allow partial answers when some evidence exists.

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**  
Think about wrong answers, missing information, or over trusting the LLM.

> This system can cause real world harm if users rely on it for critical or technical decisions without verifying the results. For instance if they are using it for authentication or system configuration, incorrect or missing information can lead to broken systems, or security issues.

**What instructions would you give real developers who want to use DocuBot safely?**  
Write 2 to 4 short bullet points.

- Always verify answers against the original docs before taking action.
- Treat "I do not know" as a signal to check the docs manually rather than forcing an answer.


---
