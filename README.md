# UA Theater — Building Ops

For Pastor Aaron, Pastor Shana, Pastor Manny, Johnny Ray, and anyone helping run the
building. Everything here is about the building itself — what it is, what shape it's in, and
how to run it. No deal pricing, contracts, or financials live in this repo; that's kept
separate on purpose.

## Start here

**[`UA-Theater-Roof-Book.pdf`](UA-Theater-Roof-Book.pdf)** — the whole HVAC picture in 9
pages. A drawn roof plan showing where every unit sits, which rooms are hot, what the panel
can and cannot reach, how to turn units on. Print it and take it on the roof.
(`roof-book.html` is the same thing as a web page if you'd rather read it on a phone.)

**[`dashboard.html`](dashboard.html)** — open in any browser while on the building's local
network for live AC status and on/off buttons. No login, no app, no internet needed.

**[`TEAM-BRIEFING.md`](TEAM-BRIEFING.md)** — the plain-language summary if you read nothing
else below.

## The rest of the building, organized

- **[`01-Drawings-and-Plans/`](01-Drawings-and-Plans/)** — floor plans, site plan, and the
  original 1998 mechanical drawing set. All PDFs, viewable in any browser.
- **[`02-3D-Model-and-Sanctuary-Plan/`](02-3D-Model-and-Sanctuary-Plan/)** — an interactive
  3D model of the whole building (`index.html`, just open it) and the sanctuary seating study
  showing how houses 106–109 could combine into one worship space.
- **[`03-Mechanical-and-HVAC/`](03-Mechanical-and-HVAC/)** — which rooftop unit serves which
  room, what's actually up there today vs. the original design, the building automation panel
  (how to log in, what it controls, what's broken vs. just dormant), and the live
  remote-control system in `HVAC-Remote-Control/` that can actually turn units on and off from
  a phone.
- **[`04-Electrical/`](04-Electrical/)** — what we know about the electrical system (a real
  inspector's findings) and what drawings we still don't have.
- **[`05-Inspection-Report/`](05-Inspection-Report/)** — the full pre-closing inspection
  report, a licensed inspector's physical walkthrough of the building.
- **[`06-Command-Center-App/`](06-Command-Center-App/)** — the volunteer job-tracking app for
  actually running the remodel. A link, not a document.

## The short version, if you read nothing else

26 rooftop units. The panel can reach 14 of them; the other 12 only respond by hand at the
unit itself. The panel's schedule still runs the old movie-theater hours and cannot be
rewritten — the software no longer exists, confirmed by BGIS. The plan is a Raspberry Pi to
run the schedule for the 14 units that answer, and thermostats on the other 12 as we get to
them. Electrical: a real inspector found the main panel (Square D, 400A, back of the
building) in service with a few fixable problems, but the full original wiring drawings are
still missing.

## Please keep this private

The Mechanical-and-HVAC section includes the building panel's login. Don't post links or
files from this repo publicly.

## Add what you learn

Drop new findings, photos, or documents in the folder that matches them so everyone has them.
