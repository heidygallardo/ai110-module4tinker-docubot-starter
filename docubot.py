"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import string
import glob

STOP_WORDS = {"which", "the", "all", "is", "are", "returns", "a", "an",
              "what", "how", "does", "do", "i", "in", "of", "to", "for"}

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, documents):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the documents
        they appear in.

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """

        index = {}

        # TODO: implement simple indexing

        # iterate through each document (filename, text)
        for filename, text in documents:

            # skip empty documents
            if not text:
                continue
            
            # normalize text
            # use set to avoid duplicate words 
            words = set(text.lower().split())

            for word in words:

                # remove punctuation from word for better matching
                word = word.strip(string.punctuation)

                # skip empty words after cleaning
                if not word:
                    continue
                
                # handle when word is not in index yet, initialize with empty list
                if word not in index:
                    index[word] = []

                # add document to index for this word if not already present
                if filename not in index[word]:
                    index[word].append(filename)

        # return completed inverted index
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """

        # TODO: implement scoring
        if not query:
            return 0
        
        # normalize query and split into words
        query_words = query.lower().split()

        # normalize text for substring matching
        text_lower = text.lower()

        score = 0

        # iterate through every word in query
        for word in query_words:

            # remove punctuation from word for better matching
            word = word.strip(string.punctuation)

            # skip empty or stop words
            if not word or word in STOP_WORDS:
                continue

            # handle when cleaned query word appears in document (substring match catches plurals/variants)
            if word in text_lower:

                # increment score for each match
                score += 1

        # return total number of query words that appear in the text as relevance score
        return score

    def retrieve(self, query, top_k=3):
        """
        TODO (Phase 1):
        Use the index and scoring function to select top_k relevant document snippets.

        Return a list of (filename, text) sorted by score descending.
        """
        results = []
        # TODO: implement retrieval logic

        if not query:
            return results

        # normalize query and split into words
        query_words = query.lower().split()


        # use set to avoid duplicate candidates
        candidates = set()

        # find candidate documents using inverted index 
        for word in query_words:

            word = word.strip(string.punctuation)

            # handle when word exists in index (appears in any document)
            if word in self.index:

                # add documents containing this word to candidates
                for filename in self.index[word]:
                    candidates.add(filename)

        # if no candidates found, return empty results
        if not candidates:
            return results

        doc_lookup = {filename: text for filename, text in self.documents}

        # score each candidate document
        scored = []

        for filename in candidates:
            text = doc_lookup[filename]

            # compute relevance score
            score = self.score_document(query, text)

            # store score with document info for sorting
            scored.append((score, filename, text))

        # sort documents by score in descending order
        scored.sort(key=lambda x: x[0], reverse=True)

        # get filename and text for top_k results
        for score, filename, text in scored:
            results.append((filename, text))

        # return only top k results
        return results[:top_k]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
