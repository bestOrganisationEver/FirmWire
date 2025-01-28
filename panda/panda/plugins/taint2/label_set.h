/* PANDABEGINCOMMENT
 *
 * Authors:
 *  Tim Leek               tleek@ll.mit.edu
 *  Ryan Whelan            rwhelan@ll.mit.edu
 *  Joshua Hodosh          josh.hodosh@ll.mit.edu
 *  Michael Zhivich        mzhivich@ll.mit.edu
 *  Brendan Dolan-Gavitt   brendandg@gatech.edu
 *
 * This work is licensed under the terms of the GNU GPL, version 2.
 * See the COPYING file in the top-level directory.
 *
PANDAENDCOMMENT */

#ifndef __LABEL_SET_H_
#define __LABEL_SET_H_

#include <cstdint>
#include <set>

typedef uint32_t TaintLabel;

extern "C" {
typedef const std::set<TaintLabel> *LabelSetP;
LabelSetP label_set_union(LabelSetP ls1, LabelSetP ls2);
LabelSetP label_set_singleton(TaintLabel label);
}

void label_set_iter(LabelSetP ls, void (*leaf)(TaintLabel, void *), void *user);
std::set<TaintLabel> label_set_render_set(LabelSetP ls);


#endif
