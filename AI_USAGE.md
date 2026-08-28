# AI Usage

I used ChatGPT while completing this assessment.

AI helped me with:

* Understanding the assignment requirements.
* Proposing a Python and FastAPI project structure.
* Drafting initial implementations for the API, deterministic generator, in-memory storage, job manager and invariant validator.
* Drafting automated tests and README documentation.
* Explaining errors encountered while installing dependencies and running the tests.

I looked through and adapted all AI-generated outputs before including it. For example, the initial tests used names like `JobStatus`, `requested_users` and `create_job`, while my code used `ScenarioStatus`, `requestedUsers` and `createJob`. I compared the suggestions with my actual source code and runtime errors, then changed the tests to match the implemented models and methods.

I also used ChatGPT to clarify whether additional background event types were needed, as they were not asked for in the assignment. ChatGPT explain that although these event types were optional, additional event generation was needed when the requested event count exceed the 5 mandatory attack-chain event. It recommended adding them to provide realistic activity around this attack so I reviewed and adopted their recommendation.

I ran the app locally and manually testing its health, scenario-creation, retrieval and error endpoints using `curl`. I also ran the complete automated test suite using `python -m pytest -v`, resulting in 36 passing tests.

The tests verified the requested user, device and event counts, ensuring that every scenario had a unique ID. It also ensured the entities were valid references, timestamps were in chronological order and the attack followed the required attack-chain ordering. Furthermore, it ensured that there was a deterministic output for same configurations and seeds and generation-failure handling.

While AI was used, I still remain responsible for understanding, testing and explaining the submitted solution.