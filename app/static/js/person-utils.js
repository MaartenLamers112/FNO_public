"use strict";

export function hasPersonName(person) {
    return (
        person.current_name !== null
        && person.current_name.trim() !== ""
    );
}