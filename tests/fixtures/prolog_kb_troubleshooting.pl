% Contract fixture only. Canonical expert implementations belong to their owner.
:- module(troubleshooting_contract,
          [diagnose/4, promote/5, recall/4]).
:- use_module(library(error)).
:- use_module(library(apply)).
:- use_module(library(lists)).

% Host observations are inert typed data. No observation is called as code.
valid_observation(observed(Id, Project, Task, Run, Revision, Signal)) :-
    maplist(atom, [Id, Project, Task, Run, Revision]),
    memberchk(Signal, [task_borrowed_success, head_only_run_key,
                       task_run_isolated, task_run_not_isolated]).

validate(Observations) :-
    must_be(list, Observations),
    ( maplist(valid_observation, Observations) -> true
    ; domain_error(diagnostic_observations, Observations) ).

signal(Observations, Project, Revision, Signal, evidence(Id, Task, Run)) :-
    member(observed(Id, Project, Task, Run, Revision, Signal), Observations).

diagnose(Observations, Project, Revision, Result) :-
    validate(Observations),
    ( signal(Observations, Project, Revision, task_run_isolated, _),
      signal(Observations, Project, Revision, task_run_not_isolated, _)
    -> Result = conflict(task_run_isolation)
    ; signal(Observations, Project, Revision, task_borrowed_success, Symptom),
      signal(Observations, Project, Revision, head_only_run_key, Cause)
    -> Result = confirmed(head_only_run_key, [Symptom, Cause])
    ; Result = unknown(insufficient_current_evidence) ).

% Promotion requires both a diagnosed cause and a tested correction.
% A hypothesis, stale observation or contradictory test cannot be promoted.
promote(Observations, Project, Revision, Version, File) :-
    must_be(integer, Version), Version > 0,
    diagnose(Observations, Project, Revision, confirmed(Cause, Evidence)),
    signal(Observations, Project, Revision, task_run_isolated, Test),
    \+ signal(Observations, Project, Revision, task_run_not_isolated, _),
    Rule = learned_rule(Project, verification_scope, Version,
                        avoid(Cause), remedy(isolate_task_run),
                        confirmed, Revision, [Test|Evidence]),
    % Exclusive creation retains previous versions instead of overwriting.
    \+ exists_file(File),
    setup_call_cleanup(open(File, write, Stream, [if_exists(error)]),
                       write_term(Stream, Rule, [quoted(true), fullstop(true), nl(true)]),
                       close(Stream)).

% Read one closed record, never consult an untrusted knowledge file.
recall(File, Project, Revision, Result) :-
    setup_call_cleanup(open(File, read, Stream),
                       (read_term(Stream, Rule, []), read_term(Stream, End, [])),
                       close(Stream)),
    ( ground(Rule), End == end_of_file,
      Rule = learned_rule(Owner, verification_scope, Version,
                           avoid(head_only_run_key), remedy(isolate_task_run),
                           confirmed, AtRevision, Evidence),
      atom(Owner), integer(Version), Version > 0, atom(AtRevision),
      is_list(Evidence), Evidence = [_|_],
      maplist(valid_evidence, Evidence)
    -> ( Owner \== Project -> Result = unknown(other_project)
       ; AtRevision \== Revision -> Result = stale(Rule)
       ; Result = available(Rule) )
    ; domain_error(learned_rule, Rule) ).

valid_evidence(evidence(Id, Task, Run)) :- maplist(atom, [Id, Task, Run]).
