# Bharat Cement Development

This csv contains a year's worth of data for the BCD plant

Unhelpfully, they only send NCV when it changes, so you only have a single value.

Cement plants are 24 x 7 operations, except when they're not.

During the year, BCD had a _shutdown_ so they could clean the junk out of the
kiln.

The raw meal and coal feed will still show _some_ value, because the scales that
weigh those out aren't entirely precise. You should not calculate or return SHC 
values for feeds that are close to zero, since they are nonsensical.
