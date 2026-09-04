:- module(prolog_knowledge_store, [main/0]).

:- use_module(library(aggregate)).
:- use_module(library(http/json)).
:- use_module(library(persistency)).

:- persistent
    knowledge(
        id:atom,
        scope:atom,
        owner:atom,
        kind:atom,
        key:atom,
        value:atom,
        source:atom,
        status:atom,
        created_at:atom,
        updated_at:atom
    ).

write_json(Dict) :-
    json_write_dict(current_output, Dict, [width(0)]),
    nl.

attach(Db) :-
    db_attach(Db, []).

record_dict(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, UpdatedAt,
            _{id:Id,
              scope:Scope,
              owner:Owner,
              kind:Kind,
              key:Key,
              value:Value,
              source:Source,
              status:Status,
              created_at:CreatedAt,
              updated_at:UpdatedAt}).

matches_filter('*', _) :- !.
matches_filter(Expected, Actual) :-
    Expected == Actual.

matches_query('*', _, _) :- !.
matches_query(Query, Key, Value) :-
    downcase_atom(Query, Needle),
    downcase_atom(Key, KeyLower),
    downcase_atom(Value, ValueLower),
    ( sub_atom(KeyLower, _, _, _, Needle)
    ; sub_atom(ValueLower, _, _, _, Needle)
    ).

put(Db, ProposedId, Scope, Owner, Kind, Key, Value, Source, Status, Stamp) :-
    attach(Db),
    ( knowledge(ExistingId, Scope, Owner, Kind, Key, _, _, _, CreatedAt, _)
    -> retractall_knowledge(_, Scope, Owner, Kind, Key, _, _, _, _, _),
       Id = ExistingId
    ;  Id = ProposedId,
       CreatedAt = Stamp
    ),
    assert_knowledge(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, Stamp),
    write_json(_{id:Id,
                 scope:Scope,
                 owner:Owner,
                 kind:Kind,
                 key:Key,
                 status:Status,
                 created_at:CreatedAt,
                 updated_at:Stamp}).

list_records(Db, ScopeFilter, OwnerFilter, KindFilter, Query, StatusFilter) :-
    attach(Db),
    findall(
        Dict,
        ( knowledge(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, UpdatedAt),
          matches_filter(ScopeFilter, Scope),
          matches_filter(OwnerFilter, Owner),
          matches_filter(KindFilter, Kind),
          matches_filter(StatusFilter, Status),
          matches_query(Query, Key, Value),
          record_dict(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, UpdatedAt, Dict)
        ),
        Records
    ),
    write_json(_{records:Records}).

applicable_scope(global, '*', _, _).
applicable_scope(project, Owner, Owner, _).
applicable_scope(session, Owner, _, Owner) :-
    Owner \== '*'.

list_applicable(Db, ProjectOwner, SessionOwner, KindFilter, Query, StatusFilter) :-
    attach(Db),
    findall(
        Dict,
        ( knowledge(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, UpdatedAt),
          applicable_scope(Scope, Owner, ProjectOwner, SessionOwner),
          matches_filter(KindFilter, Kind),
          matches_filter(StatusFilter, Status),
          matches_query(Query, Key, Value),
          record_dict(Id, Scope, Owner, Kind, Key, Value, Source, Status, CreatedAt, UpdatedAt, Dict)
        ),
        Records
    ),
    write_json(_{records:Records}).

set_status(Db, Id, NewStatus, Stamp) :-
    attach(Db),
    ( knowledge(Id, Scope, Owner, Kind, Key, Value, Source, _, CreatedAt, _)
    -> retractall_knowledge(Id, _, _, _, _, _, _, _, _, _),
       assert_knowledge(Id, Scope, Owner, Kind, Key, Value, Source, NewStatus, CreatedAt, Stamp),
       write_json(_{id:Id, status:NewStatus, updated_at:Stamp})
    ;  throw(error(existence_error(knowledge, Id), _))
    ).

forget(Db, Id) :-
    attach(Db),
    ( knowledge(Id, _, _, _, _, _, _, _, _, _)
    -> retractall_knowledge(Id, _, _, _, _, _, _, _, _, _),
       write_json(_{id:Id, deleted:true})
    ;  throw(error(existence_error(knowledge, Id), _))
    ).

health(Db) :-
    attach(Db),
    aggregate_all(count, knowledge(_, _, _, _, _, _, _, _, _, _), Count),
    write_json(_{status:ok, records:Count}).

dispatch([Db, put, Id, Scope, Owner, Kind, Key, Value, Source, Status, Stamp]) :- !,
    put(Db, Id, Scope, Owner, Kind, Key, Value, Source, Status, Stamp).
dispatch([Db, list, Scope, Owner, Kind, Query, Status]) :- !,
    list_records(Db, Scope, Owner, Kind, Query, Status).
dispatch([Db, applicable, ProjectOwner, SessionOwner, Kind, Query, Status]) :- !,
    list_applicable(Db, ProjectOwner, SessionOwner, Kind, Query, Status).
dispatch([Db, status, Id, NewStatus, Stamp]) :- !,
    set_status(Db, Id, NewStatus, Stamp).
dispatch([Db, forget, Id]) :- !,
    forget(Db, Id).
dispatch([Db, health]) :- !,
    health(Db).
dispatch(Argv) :-
    throw(error(domain_error(knowledge_store_argv, Argv), _)).

main :-
    current_prolog_flag(argv, Argv),
    catch(
        dispatch(Argv),
        Error,
        ( message_to_string(Error, Message),
          write_json(_{status:error, error:Message}),
          halt(2)
        )
    ),
    halt(0).

:- initialization(main, main).
