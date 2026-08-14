# Detailed (disorganized) brain dump notes

## High level stuff

At the highest level, the prototype is performing AI-mediated deliberation between two participants who genuinely disagree (perhaps not on everything, but on some parts of a problem/issue). The premise is that AI might improve civic discourse by helping people reason with each other, rather than simply giving each individual a private assistant to "optimize" doing a task. 

But that creates a interesting problem: the moderator inherently has some degree of power over the conversation, simply by deciding what deserves attention (e.g., what to respond to/ interject on): what deserves skepticism, what context gets supplied, when to intervene, and how to characterize disagreements. All the while, the intervention policy should make disagreement more productive without the moderator becoming a third participant in the conversation. (This of course bakes in a notion of what it means to be a "participant", which is also hard; I think the moderator probably is a participant to some extent. That's unavoidable. But it's one with clear rules around supporting productive disagreement for the two human participants.)

This is why neutrality is so important. For instance, a moderator can be perfectly polite and but never explicitly say "Bob is right" but still have substantial influence on the direction of the conversation. E.g., the moderator might challenge Bob's factual claims while letting Alice's assumptions pass; summarize Alice's take more sympathetically; find stronger evidence for Bob; tell Alice that she hasn't responded to an objection raised by Bob (while overlooking this for Bob re: Alice). These are all things relevant to the moderator's decisions (and they also operate in concert). 

## I think there are three components overall, conceptually

1. The first part is what the participants actually experience the debate. The moderator should identify when the participants are answering different questions, surface neglected claims, clarify terms, identify common ground, bring in outside evidence (when evidence would actually resolve something; and so that also involves some deliberation, not just when to search for it, but when/what to surface), and perhaps periodically summarize the state of the conversation/ where it has landed. But it shouldn't constantly interrupt (that'd make it too active a participant), and may actually crowd out the human participants. 

2. The second part relates to some of the open questions about the datamodel. We probably need some internal representation of the debate" tracking claims, rebuttals, open questions, and agreements. My gut tells me that means not just taking the transcript and feeding it to the Claude API (but maybe this is something we can test; we can do both that and something like below). That is, the app can maintain lightweight structured state about a session such as:

- positions or claims each participant has actually endorsed;
- support/rebuttal relationships;
- questions awaiting answers;
- propositions on which they agree;
- candidate core points of disagreement/cruxes;
- factual questions that external evidence might resolve;
- a history of the moderator's actions (both surfaced in the conversation, and also what isn't surfaced maybe) so that intervention is balanced (and by this I don't mean 50% for Alice, 50% for Bob; this is a harder thing to think through than that).

Something this could look like? (which is also useful for making the prototype instrumentable/ can read in transcripts and reason abou them) is that every moderator interaction could be a cycle/ state machine of some kind, like:

transcript state --> decision --> intervention type --> intervention text [or no-op] --> state update

I think is could be really useful later for the bias evaluation part. We could ask whether the bias came from:

- deciding to intervene against one side more often;

- classifying one person's statement as requiring evidence; 

- identifying one person's claim as the crux for the whole debate;

- retrieving different information; or,

- wording substantively equivalent interventions differently / with different tone.

3. We need something for oversight/evaluation. We will need to have a way of testing waht it means for the moderator to be exhibiting biased behavior, in a way that we can develop concrete (falsifiable) claims. Some initial thoughts on this:
- Counterfactuals? We could give the system essentially identical debates but swap participant identities/ swap which speaker holds which position; we could chagne other things, like speaker confidence/style (while retaining the substantive argument). The main idea is create paired transcripts, and see what the impact is on moderator behavior (and our judgments of bias). Possible things to measure that could inform an operationalization of "bias":  differences in things like intervention frequency, amount of explanatory text provided, requests for justification, strength of skeptical language, factual verification effort, praise/deference, framing in summaries, and so on. 

## Productive disagreement

This is the main goal. The goal can't be for the moderator to direct the users to try to come to a place of agreement. That's not what the point of this is. 

For instance, a successful debate might end with a much sharper disagreement. E.g., "We agree about X, Y, and Z; but our remaining difference is that Alice puts considerably more weight on value P while Bob puts more weight on Q," or "Everything now turns on this uncertain propostion, which requires more empirical evidence to continue the debat." This kind of thing would actually be a useful/positive outcome. Tl;dr: convergence of the human participants isn't the goal here. (A lot more on this below re: thinkers that are informing my thinking on this.)

Another way to see this is that the moderator can help the participants see the debate's structure, prompt participants to engage with one another's strongest claims, and fill informational gaps where outside facts are genuinely useful. But it shouldn't synthesize "correct" or "incorrect" conclusions for the participants. In other words, the participants are still doing the normative work here.

## Writers that this assignment immediately called to me

Isaiah Berlin and Jurgen Habermas.

I am going to try to keep this brief, because I don't want to drift too much. But I think a little background here is important. Both have things to say about how the app can be strongly directional about the *process* of reasoning while being deliberately non-directional about the *substantive* outcome. This procedure/substance divide seems really core to me. This feels core to the whole assignment. 

### Why Berlin is relevant in my thinking

Value pluralism is the key idea here. A lot of AI systems behave like disagreement is an obstacle/ a thing to solve, with convergence at the end marking a successful interaction. But that premise isn't right, and Berlin rejects it altogether (and has been influential in my thinking/research). The crib notes version is: 

Reasonable people can face genuine conflicts among values that can't simply be reduced to some common metric. Liberty, equality, security, fairness, autonomy, community, efficiency, democratic accountability, etc. can come into real tension. It might very well be the case that there are no new facts that can come to light that would make the disagreement go away. 

To make this concrete for the chosen Buoy topic, suppose that the two participants eventually establish the following: 

We agree about the likely economic effects of congestion pricing. We disagree because one of us regards distributional fairness as overriding the efficiency gain in these circumstances, while the other does not.

This would actually be a good outcome! Buoy helped reach this point of clarity, even though there isn't full convergence. 

I think the tl;dr is: clarification of persistent disagreement is itself progress/success in this system. This can be founded in genuine normative differences. And that is also where a convesration can end/ that can basically be teh crux (and Buoy could  call this out, without trying to actually adjudicate the disagreement).

An aside, I think less relevant to stay focused: But something I've been thinking about a lot is Berlin's work on monoism; and here that would be sort of disguised as neutrality. E.g., Claude could quietly assume that every dispute has a uniquely rational resolution, and then frame the discussion around getting everyone there. That could "look" reasonable or unbiased but actually is biased.

### Habermas

The point here is keeping in mind the conditions underwhich discourse is/remains legitimate. Buoy shouldn't be some oracle that resolves the dispute. Its job is to improve the conditions under which the participants can give and respond to reasons they give each other.

That articulates, I think, the following things the AI should try to pay attention to:

- each participant can actually make their position intelligible;
- claims and reasons receive responses rather than being ignored;
- participants are responding to what the other person actually said;
- one person isn't gaining an advantage merely through their style/confidence/repetition/tone 
- relevant factual uncertainty is clear/visible;
- participants can challenge each other, but also the moderator.

That last part actually seems important for contestability. Concretely, if the moderator says "It seems your disagreement i primarily about X" then either participants should be able to say "No, it's not, it's about Y." And that should influence the converastion. 

Another key point along these lines re: legitimacy of the discourse is for Claude to apply the same criteria for deciding what needs clarification, evidence, skepticism, or intervention (regardless of who said it or which conclusion it supports).

And this then relates to the evaluation idea I mention elsewhere for bias. We can perform role/position swaps. And then if the exact same empirical claim moves from Alice to Bob, does Buoy become more or less skeptica or change its behavior in other ways? (This is where structured transcripts are useful for instrumenting/ re-running converations, or at least seeding them with the same starts.) for another example, if an identical argument is used for the opposite political conclusion in a similar case, does the moderator suddenly demand more evidence? Stuff like that. This I think gets us closer to things we can measure, an ability to falsify neutrality/ claim bias. 

## Where this leaves things

I cut myself off for time (I'm almost at the end of the time that I have today to work on this; will have to finish tomorrow/ get back to my job). But I think this leaves us with the following. Maybe we need some kind of mini constitution for this system, not just a system prompt? 

1. Serve the participants' deliberation, not a preferred conclusion.

2. Be directive about conversational *process*, but restrained about *substantive* judgments.

3. Treat clarified disagreement as success. Don't optimize for consensus.

4. Apply the same intervention criteria irrespective of participant or position.

5. Correct factual errors when warranted/appropriate, but don't start advocating for either participant or their position.

6. Use the minimum intervention needed (so as to not distract from the exchange taking place).

7. Allow for interpretations and summaries to be contestable by the participants.

8. Track the moderator's allocation of attention, as this is something that can also be biased.

## Miscellanea/ open questions

Does the model see every message as it arrives?

Is it invoked after every turn, even if it ultimately says "don't intervene"?

Does it receive the entire raw transcript, or a transcript plus structured debate state?

Does one model call both decide whether to intervene and determine what to say?

Or do we separate an observer/controller from the model that writes the intervention?

Does the model update some private structured representation after every message?

When factual information is needed, is retrieval/search initiated by the moderator or participant(s)?

What information about previous moderator actions does the model see?

How do we prevent accumulated summaries from silently distorting one participant's position?

What information should the participants see?

## Look-ahead note

As a look ahead, I'll want to pause/ reflect on this in relation to the assignment spec to make sure we're touching on the design requirements by addressing these ponits. So we will want to start developing a checklist file for the assignment requirements (that we can check off), which is at a different level of abstraction than our task checklist. (The task checklist is useful for our work together; the assignment one is useful for making sure I stay on task to finish what's been asked of me.)