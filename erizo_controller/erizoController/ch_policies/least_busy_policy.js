const logger = require('../../common/logger').logger;
const log = logger.getLogger('LeastBusyPolicy');

/*
Params

	agents: object with the available agents
		agent_id : {
        	info: {
        		id: String,
        		rpc_id: String
        	},
        	metadata: Object,
        	stats: {
				perc_cpu: Int
        	},
			timeout: Int		// number of periods during the agent has not respond
   	 	}

Returns

	rpc_id: agent.info.rpc_id field of the selected agent.
		*default value: "ErizoAgent" - select the agent in round-robin mode

*/
exports.getErizoAgent = function (agents) {
	'use strict';
	if (agents) {
		log.info(`All agents ${JSON.stringify(agents)}`);
		const agentsArray = [];
		let selectedAgent;
		for (const agentId in agents) {
			const agent = agents[agentId];
			// If the agent has not been responding then give it a break;
			if (agent.timeout > 5) {
				continue;
			}
			if (agent.stats && agent.stats.perc_cpu) {
				if (selectedAgent) {
					if (selectedAgent.stats.perc_cpu > agent.stats.perc_cpu) {
						selectedAgent = agent;
					}
				} else {
					selectedAgent = agent;
				}
			}
			// If we don't have stats then default it to half busy
			// if (!agent.stats) {
			// 	agent.stats = {
			// 		perc_cpu: 0.5,
			// 	};
			// }
			// if (!agent.stats.perc_cpu) {
			// 	agent.stats.perc_cpu = 0.5;
			// }
			// agentsArray.push({
			// 	rpc_id: agent.info.rpc_id,
			// 	cpu: agent.stats.perc_cpu,
			// });
		}
		if (selectedAgent) {
			log.info(`Selected agent ${JSON.stringify(selectedAgent)}`);
			return selectedAgent.info.rpc_id;
		}
		// if (agentsArray.length > 0) {
		// 	agentsArray.sort((a, b) => {
		// 		return a.cpu - b.cpu;
		// 	});
		// 	console.log(`LOOK AT ME: ${JSON.stringify(agentsArray[0])}`);
		// 	return agentsArray[0].rpc_id;
		// }
	}
	return 'ErizoAgent';
};
