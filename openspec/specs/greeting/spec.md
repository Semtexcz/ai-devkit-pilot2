# greeting Specification

## Purpose
Provide a command-line greeting with an optional name while retaining the
existing script invocation and default output.

## Requirements

### Requirement: Named greeting

The script SHALL accept an optional `--name` argument with a name value and print
`Hello from <name>!` followed by one newline to stdout, with no other stdout,
empty stderr and exit status zero.

#### Scenario: Greet Ada

- **WHEN** the user runs `python main.py --name Ada`
- **THEN** stdout is exactly `Hello from Ada!\n`, where `\n` denotes one newline
- **AND** stderr is empty and the exit status is zero

### Requirement: Default greeting

The script SHALL print the existing default greeting when `--name` is omitted.

#### Scenario: Omit the name

- **WHEN** the user runs `python main.py`
- **THEN** stdout is exactly `Hello from ai-devkit-pilot2!\n`, where `\n` denotes one newline
- **AND** stderr is empty and the exit status is zero

### Requirement: Command-line help

The script SHALL provide help through `--help` that documents `--name` and its
name value, exits successfully and does not print a greeting.

#### Scenario: Discover the name argument

- **WHEN** the user runs `python main.py --help`
- **THEN** stdout contains usage information describing `--name` and its name value
- **AND** stderr is empty, the exit status is zero and no greeting is printed

### Requirement: Invalid arguments

The script SHALL reject unknown arguments and a missing value for `--name`,
write a diagnostic explaining the argument error to stderr, print no greeting
and exit with a nonzero status. Exact diagnostic wording and nonzero status
value are not prescribed.

#### Scenario: Unknown argument

- **WHEN** the user runs `python main.py --unknown`
- **THEN** the exit status is nonzero and stderr identifies `--unknown` as unrecognized
- **AND** stdout is empty

#### Scenario: Name value missing

- **WHEN** the user runs `python main.py --name`
- **THEN** the exit status is nonzero and stderr explains that `--name` requires a value
- **AND** stdout is empty

### Requirement: No additional runtime dependency

The greeting capability MUST run with the project's supported Python interpreter
without installing any third-party runtime package.

#### Scenario: Run without third-party runtime packages

- **GIVEN** the supported Python interpreter is available without third-party packages
- **WHEN** the user runs the named greeting, default greeting and help commands
- **THEN** all three commands satisfy their respective success scenarios without installing packages

### Requirement: Backward-compatible script entry point

The existing `main.py` entry point and no-argument execution through the project's
documented start command SHALL remain available without invocation changes.
The newly specified argument validation applies to invalid invocations.

#### Scenario: Existing project start command

- **GIVEN** the existing project environment is prepared
- **WHEN** the user runs `mise run start`
- **THEN** the application prints exactly `Hello from ai-devkit-pilot2!` followed by one newline
- **AND** the command succeeds without requiring new arguments or runtime dependencies
