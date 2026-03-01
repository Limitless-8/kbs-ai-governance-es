% prolog/json_writer.pl
% Minimal JSON writer helpers (no external libs).
% We only emit JSON objects/arrays/strings/numbers/booleans/null.

:- module(json_writer, [
    json_write_kv_pairs/1,
    json_write_obj/1,
    json_write_arr/1,
    json_write_string/1,
    json_write_atom_string/1,
    json_write_bool/1,
    json_write_null/0
]).

json_write_obj(Pairs) :-
    write('{'),
    json_write_kv_pairs(Pairs),
    write('}').

json_write_kv_pairs([]).
json_write_kv_pairs([K=V]) :-
    json_write_string(K),
    write(':'),
    json_write_value(V).
json_write_kv_pairs([K=V|Rest]) :-
    json_write_string(K),
    write(':'),
    json_write_value(V),
    write(','),
    json_write_kv_pairs(Rest).

json_write_arr([]) :-
    write('[]').
json_write_arr(List) :-
    write('['),
    json_write_arr_items(List),
    write(']').

json_write_arr_items([]).
json_write_arr_items([X]) :-
    json_write_value(X).
json_write_arr_items([X|Xs]) :-
    json_write_value(X),
    write(','),
    json_write_arr_items(Xs).

json_write_value(S) :-
    string(S), !,
    json_write_string(S).
json_write_value(A) :-
    atom(A), !,
    json_write_atom_string(A).
json_write_value(N) :-
    number(N), !,
    write(N).
json_write_value(true) :- !, write('true').
json_write_value(false) :- !, write('false').
json_write_value(null) :- !, json_write_null.
json_write_value(obj(Pairs)) :- !, json_write_obj(Pairs).
json_write_value(arr(List)) :- !, json_write_arr(List).
json_write_value(V) :-
    % fallback: stringify unknown terms
    term_string(V, S),
    json_write_string(S).

json_write_string(S) :-
    string_chars(S, Chars),
    write('"'),
    json_write_escaped_chars(Chars),
    write('"').

json_write_atom_string(A) :-
    atom_string(A, S),
    json_write_string(S).

json_write_bool(true) :- write('true').
json_write_bool(false) :- write('false').

json_write_null :- write('null').

json_write_escaped_chars([]).
json_write_escaped_chars(['"'|T]) :- write('\\\"'), json_write_escaped_chars(T).
json_write_escaped_chars(['\\'|T]) :- write('\\\\'), json_write_escaped_chars(T).
json_write_escaped_chars(['\n'|T]) :- write('\\n'), json_write_escaped_chars(T).
json_write_escaped_chars(['\r'|T]) :- write('\\r'), json_write_escaped_chars(T).
json_write_escaped_chars(['\t'|T]) :- write('\\t'), json_write_escaped_chars(T).
json_write_escaped_chars([C|T]) :- write(C), json_write_escaped_chars(T).
