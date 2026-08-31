"use strict";

import { getNormalizedImagePosition } from "./coordinates.js";

const OVERLAY_PREFIX = "detection-proposal-";

export class DetectionProposalManager {
    constructor({ viewer, overlayManager, dragManager, onSelect, onChange }) {
        this.viewer = viewer;
        this.overlayManager = overlayManager;
        this.dragManager = dragManager;
        this.onSelect = onSelect;
        this.onChange = onChange;
        this.proposals = [];
        this.overlayIds = new Set();
        this.selectedId = null;
    }

    setProposals(proposals, firstLabelNumber) {
        this.proposals = proposals.map((proposal, index) => ({
            ...proposal,
            label_number: firstLabelNumber + index,
        }));
        this.selectedId = null;
        this.render();
    }

    render() {
        this.#removeOverlays();
        if (!this.proposals.length) return;

        const renderNow = () => {
            const tiledImage = this.viewer.world.getItemAt(0);
            if (!tiledImage) return;
            for (const proposal of this.proposals) {
                this.#addProposal(proposal, tiledImage);
            }
        };

        if (this.viewer.world.getItemCount() > 0) {
            renderNow();
        } else {
            this.viewer.addOnceHandler("open", renderNow);
        }
    }

    select(proposalId) {
        this.selectedId = proposalId;
        for (const id of this.overlayIds) {
            this.overlayManager.getElement(id)?.classList.toggle(
                "detection-proposal--selected",
                id === this.#overlayId(proposalId),
            );
        }
    }

    clearSelection() {
        this.selectedId = null;
        for (const id of this.overlayIds) {
            this.overlayManager.getElement(id)?.classList.remove(
                "detection-proposal--selected",
            );
        }
    }

    removeSelected() {
        if (!this.selectedId) return false;
        this.proposals = this.proposals.filter(
            (proposal) => proposal.proposal_id !== this.selectedId,
        );
        this.selectedId = null;
        this.#renumber();
        this.render();
        this.onChange?.(this.proposals);
        return true;
    }

    clear() {
        this.proposals = [];
        this.selectedId = null;
        this.#removeOverlays();
        this.onChange?.(this.proposals);
    }

    getProposals() {
        return this.proposals.map((proposal) => ({ ...proposal }));
    }

    #addProposal(proposal, tiledImage) {
        const imageSize = tiledImage.getContentSize();
        const imagePoint = new window.OpenSeadragon.Point(
            proposal.x_position * imageSize.x,
            proposal.y_position * imageSize.y,
        );
        const viewportPoint = tiledImage.imageToViewportCoordinates(imagePoint);
        const element = document.createElement("button");
        element.type = "button";
        element.className = "person-label detection-proposal";
        element.textContent = String(proposal.label_number);
        element.title = `AI-voorstel (${Math.round(proposal.confidence * 100)}% zeker)`;
        element.setAttribute("aria-label", element.title);
        element.addEventListener("click", (event) => {
            event.stopPropagation();
            this.onSelect?.(proposal.proposal_id);
        });

        const overlayId = this.#overlayId(proposal.proposal_id);
        this.overlayManager.add({
            id: overlayId,
            element,
            location: viewportPoint,
            placement: window.OpenSeadragon.Placement.CENTER,
            metadata: { proposal },
        });
        this.overlayIds.add(overlayId);

        this.dragManager?.register({
            overlayId,
            element,
            onDragStart: () => this.onSelect?.(proposal.proposal_id),
            onDragEnd: ({ moved, viewportPoint: newViewportPoint }) => {
                if (!moved || !newViewportPoint) return;
                const position = getNormalizedImagePosition({
                    tiledImage,
                    viewportPoint: newViewportPoint,
                });
                proposal.x_position = position.xPosition;
                proposal.y_position = position.yPosition;
                this.onChange?.(this.proposals);
            },
        });
    }

    #renumber() {
        const first = this.proposals[0]?.label_number ?? 1;
        this.proposals.forEach((proposal, index) => {
            proposal.label_number = first + index;
        });
    }

    #removeOverlays() {
        for (const overlayId of this.overlayIds) {
            this.overlayManager.remove(overlayId);
        }
        this.overlayIds.clear();
    }

    #overlayId(proposalId) {
        return `${OVERLAY_PREFIX}${proposalId}`;
    }
}
